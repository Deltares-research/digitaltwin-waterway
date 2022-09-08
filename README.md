# Digital Twin for Waterways
Code and notebooks for the Digital Twin Waterway

# Topological network of the Dutch Fairway Information System 

## Website

The v1.1 version of the [Digital Twin Waterways](https://v0-1-1--digitwin-waterways.netlify.app/) can be found online. 
The latest version of the [Digital Twin Waterways](https://digitwin-waterways.netlify.app/) is also up. 


## Files

`network_digital_twin_v0.1.yaml`
This is the NetworkX file for the Rhine corridor extending from Rotterdam (NLD) to Basel (Switzerland). 


`network_digital_twin_v0.1.geojson`
This is the geojson file for the Rhine corridor extending from Rotterdam (NLD) to Basel (Switzerland). 

## Methodological information
Sharing and Access information
Data is processed to be topological connected and to be used for (water) transport network analysis. For details see Build_FIS_network.ipynb.

Source data for the network is available at https://www.vaarweginformatie.nl/.


## Add a KPI
- Go to notebooks/kpi/chart_generation.ipynb
- Add and test a new KPI. Make a function that takes results as input and generates an echart as output
- Add the function to server.py as a new url
- Test the new api in postman
- Add the new api call in the store, in the fetchKPI action
- Add the new variable to the store using a mutation to the state
- Map the state to the KPI component
- Add the chart to the KPI component.

## Sharing and Access information

CC BY-SA 4.0 license applies: https://creativecommons.org/licenses/by-sa/4.0/.







