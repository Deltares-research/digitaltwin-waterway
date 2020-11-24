module.exports = {
  transpileDependencies: ['vuetify'],
  chainWebpack: config => {
    config.module.rules.delete('svg')
  },
  configureWebpack: {
    module: {
      rules: [
        {
          test: /\.svg$/,
          loader: 'vue-html-loader'
        }
      ]
    }
  }
}
