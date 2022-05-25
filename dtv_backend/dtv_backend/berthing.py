"""
This module provides the class CanBerth. This object can be used for finding
berth places on a route from a source to destination node on a graph.

Foreseen improvements to berthing:
- Some berths may only be reached after passing a lock. These should be
excluded, or their ETA's should be made more realistic;
- Berth place availability and dimensions should be added and should comply
with the ship's dimensions;
- ETA's are now solely distance and speed based. This could be more realistic.
"""
import datetime
import pandas as pd
import networkx as nx

import dtv_backend.logbook
import dtv_backend.scheduling
from dtv_backend.fis import shorted_path, compute_path_length


#%%
class CanBerth(dtv_backend.scheduling.HasTimeboard, dtv_backend.logbook.HasLog):
    """
    Class to find berths on a route. The CanBerth class is initiated with
    an environment, and a graph. The parameters berth_keyword and distance are
    used to identiify berth-nodes and the distance property of the graphs
    edges respectively.

    Parameters
    ----------
    env : simpy environment
        The simpy environment applicable.
    graph : networkx graph
        The graph in which to travel. Note: the graph may also be part of the
        environment, but that is not the case by default.
    berth_keyword : str, optional
        This string is used to look for berths in the graph. A node in the
        graph is said to be a berth place if its name starts with this berth_keyword.
        The default is 'Berth'.
    distance : str, optional
        The graphs egde distances are stored in this parameter. The default
        is 'length_m'.

    """

    def __init__(
        self,
        env,
        graph=None,
        berth_keyword="Berth",
        edge_distance="length_m",
        *args,
        **kwargs,
    ):
        """Initialize with an environment, a graph and keys."""
        super().__init__(env=env)

        # process the parameters
        # self.env = env
        if graph is None:
            self.graph = env.FG
        else:
            self.graph = graph
        self.berth_keyword = berth_keyword
        self.edge_distance = edge_distance

        # self.pass_node_subscribers.append(self.pass_berth)

    @property
    def __time_now(self) -> datetime.datetime:
        """Get the current time from the environment."""
        return datetime.datetime.fromtimestamp(self.env.now)

    def __is_berth(self, n) -> bool:
        """Check if node index starts with berth_keyword."""
        return n.startswith(self.berth_keyword)

    def __find_path(self, src_node, dst_node) -> list:
        """Finds a path (list of nodes)  from src to dst on the given graph."""
        return shorted_path(self.graph, src_node, dst_node)

    def __find_berths_near_route(self, src_node, dst_node, max_distance=1000):
        """
        Looks for berth places within a given maximum distance on a path form
        a source node to a destination node on the graph.
        """
        # determine the path
        path = self.__find_path(src_node, dst_node)

        # capture feasible berths in a set
        berths = set()

        # loop the nodes in the path
        for node in path:
            # generate a subgraph within given distance of the node
            new_graph = nx.generators.ego_graph(
                self.graph, node, radius=max_distance, distance=self.edge_distance
            )
            # look for berths
            candidate_berths = [n for n in new_graph.nodes if self.__is_berth(n)]
            berths = berths.union(set(candidate_berths))

        return list(berths)

    def __compute_eta_per_berth(self, src_node, dst_node, berth_nodes, mean_speed):
        """
        Computes the estimated times of arrival (ETA) at a given set of
        berths (possibly including the destination node), assuming that the
        current location is the specified source node. ETA's are currently
        solely computed based on a given mean speed, and the distances to be
        traveled accross the edges of the graph.

        Note: if the destination node is also a feasible berth, this should
        explicitly be included in the list of berth nodes!

        Method return a dataframe with for each of the specified berths the
        (1) distance from the src node, (2) the duration from to reach this
        berth node, (3) the mean-speed-based ETA based on the curren time, (4)
        the distance from the berth to the final destination.
        """
        # compute the ETA of all candidate nodes from the current node
        rows = []
        for berth in berth_nodes:
            # get the path from src_node to berth and compute distance and speed-based duration
            path_src_to_node = self.__find_path(src_node, berth)
            distance_src_to_node = compute_path_length(self.graph, path_src_to_node)
            duration_src_to_node = distance_src_to_node / mean_speed

            # compute the distance from berth to destination
            path_node_to_dst = self.__find_path(berth, dst_node)
            distance_node_to_dst = compute_path_length(self.graph, path_node_to_dst)

            # define a row to add to rows
            row = {
                "berth": berth,
                "distance from src": distance_src_to_node,
                "duration from src": duration_src_to_node,
                "eta": self.__time_now
                + datetime.timedelta(seconds=duration_src_to_node),
                "distance to dst": distance_node_to_dst,
            }

            # add the row
            rows.append(row)

        # convert to dataframe
        df = pd.DataFrame(rows)

        # compute the distance of the direct path from src to dst
        direct_path = self.__find_path(src_node, dst_node)
        direct_distance = compute_path_length(self.graph, direct_path)

        # remove berths which take us away from the destination
        df = df.loc[df["distance to dst"] <= direct_distance]

        return df

    def __find_best_berth(self, df, max_timestamp):
        """
        Selects the 'best berth' based on the output of
        ``self.__compute_eta_per_berth()``, and a maximum time at which a berth
        must be reached. The 'best berth' is defined as the berth that can be
        reached within the time limit, and brings us closest to the final
        destination node. If no such berth exists, then the berth is selected
        that can be reached within minimal time.
        """
        df["feasible"] = df["eta"] <= max_timestamp

        # get the berth which minimizes the distance to the destination
        if sum(df["feasible"]) == 0:
            # select the one in minimal time?
            next_berth = df.loc[df["eta"].idxmin(), "berth"]
        else:
            df_feas = df.loc[df["feasible"]]
            next_berth = df_feas.loc[df_feas["distance to dst"].idxmin(), "berth"]

        return next_berth

    def find_berth(
        self,
        src_node,
        dst_node,
        max_timestamp,
        max_distance,
        mean_speed,
        include_dst=True,
    ):
        """
        For a given source and destination node on the graph this method will
        suggest the next berth place which can be reached before a maximum
        time within a specified distance deviation from the path from source
        to destination. Estimations for arrival times are based on a mean
        traveling speed.

        Parameters
        ----------
        src_node : str
            Name of the source node in the graph. Assumed that the object is
            currently (timewise) at this node.
        dst_node : str
            Name of the final destination.
        max_timestamp : datetime.datetime
            Timestamp before which a berth place must me reached.
        max_distance : numeric
            Tha maximum distance to deviate from the original path from src to
            dst to look for berthing places.
        mean_speed : numeric
            The mean speed used to compute the estimated times of arrival for
            the available berths.
        include_dst : boolean, optional
            Determines whether the final destination node must be added to the
            berthing places. If True, the method will check if the final
            destination can be reached within the maximum timestamp, and is
            returned if so (hence, no berthing is needed). The default is True.

        Returns
        -------
        berth, str
            The string name of the suggested berth in the graph.
        """
        # get the berths based on the selected max deviation from route
        berths = self.__find_berths_near_route(
            src_node=src_node, dst_node=dst_node, max_distance=max_distance
        )

        # check if any feasible berths are found, else continue
        if len(berths) == 0:
            print(
                f'No berths were found on the route from src "{src_node}" '
                f'to dst "{dst_node}" with a maximum distance deviation '
                f"of {max_distance}"
            )
            return None
        else:
            # include the destination if regarded as an option
            if include_dst:
                berths += [dst_node]

            # compute the ETA's for all berths
            eta_df = self.__compute_eta_per_berth(
                src_node=src_node,
                dst_node=dst_node,
                berth_nodes=berths,
                mean_speed=mean_speed,
            )

            # use the output to suggest the best berth
            berth = self.__find_best_berth(df=eta_df, max_timestamp=max_timestamp)

            return berth

    def move_to_with_berth(self, destination, mean_speed, max_distance, limited=False):
        """
        Wrapper around the self.move_to method to move a ship from src
        to dst, but now with berthing

        [!] Note: this method assumes that self has a method 'move_to'
        """
        current_node = self.node

        while current_node != destination.node:
            # if we're not at the dst we must find the next berth (dst included)
            next_berth = self.find_berth(
                src_node=current_node,
                dst_node=destination.node,
                max_timestamp=self.next_off_duty,
                max_distance=max_distance,
                mean_speed=mean_speed,
                include_dst=True,
            )

            # sail from current to next_berth
            # next_berth_geom = self.graph.nodes[next_berth]
            yield from self.move_to(destination=next_berth, limited=limited)

            # once the berth is reached, wait until the next duty
            yield from self.sleep_till_next_duty()

            # set current to berth to continue
            current_node = next_berth

    # def pass_berth(self, node):
    #     if node == berth:
    #         yield from self.sleep_till_next_duty()
