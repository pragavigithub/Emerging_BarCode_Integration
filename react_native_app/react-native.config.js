module.exports = {
  dependencies: {
    'react-native-sqlite-storage': {
      platforms: {
        android: {
          sourceDir: '../node_modules/react-native-sqlite-storage/platforms/android',
          packageImportPath: 'io.liteglue.SQLitePluginPackage',
        },
        ios: null, // Disable iOS platform to fix configuration warning
      },
    },
    'react-native-reanimated': {
      platforms: {
        android: null,
        ios: null,
      },
    },
    'react-native-camera': {
      platforms: {
        android: null, // Disable to avoid variant conflicts
        ios: null,
      },
    },
  },
};