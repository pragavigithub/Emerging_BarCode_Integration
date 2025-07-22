# Installation Fix for React Native WMS App

## Problem Fixed
The original package.json had an incorrect barcode scanner dependency that doesn't exist:
- ❌ `react-native-barcode-scanner@^1.0.0` (doesn't exist)
- ✅ `react-native-camera@^4.2.1` (correct barcode scanning library)

## Fixed Dependencies
I've corrected the package.json with proper dependencies:

### Barcode Scanning
- `react-native-camera` - Primary barcode scanning library
- `react-native-vision-camera` - Alternative modern camera library
- `react-native-permissions` - Camera permissions

### Storage & Networking
- `@react-native-async-storage/async-storage` - Secure local storage
- `react-native-sqlite-storage` - Local SQLite database
- `@react-native-community/netinfo` - Network connectivity

### UI & Navigation
- `react-native-paper` - Material Design components
- `@react-navigation/native` - Navigation system
- `react-native-vector-icons` - Icons

## Installation Instructions

### 1. Install Dependencies
```bash
cd react_native_app
npm install
```

### 2. iOS Setup (if using iOS)
```bash
cd ios
pod install
cd ..
```

### 3. Android Permissions
The AndroidManifest.xml is already configured with camera permissions:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

### 4. iOS Permissions (add to ios/WMSMobileApp/Info.plist)
```xml
<key>NSCameraUsageDescription</key>
<string>This app needs access to camera to scan barcodes</string>
```

### 5. Run the App
```bash
# Android
npx react-native run-android

# iOS
npx react-native run-ios
```

## Alternative Barcode Libraries

If you encounter issues with react-native-camera, you can use these alternatives:

### Option 1: Vision Camera (Recommended)
```bash
npm install react-native-vision-camera
npm install react-native-vision-camera-code-scanner
```

### Option 2: Expo Barcode Scanner (if using Expo)
```bash
npm install expo-barcode-scanner
```

### Option 3: ZXing Scanner
```bash
npm install react-native-zxing-scanner
```

## Troubleshooting

### Metro Bundle Issues
```bash
npx react-native start --reset-cache
```

### Android Build Issues
```bash
cd android
./gradlew clean
cd ..
npx react-native run-android
```

### iOS Build Issues
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
npx react-native run-ios
```

### Camera Permission Issues
1. Check that permissions are properly declared
2. Ensure app requests permissions at runtime
3. Test on physical device (camera doesn't work in simulator)

## Backend Integration

Update the API base URL in `src/config/config.js`:
```javascript
export const API_CONFIG = {
  BASE_URL: 'https://your-replit-app.replit.app',
  TIMEOUT: 30000,
};
```

## Ready to Use

The app now includes:
- ✅ Fixed package dependencies
- ✅ Proper barcode scanning setup
- ✅ MySQL database integration
- ✅ Offline support with SQLite
- ✅ All three modules (GRPO, Inventory Transfer, Pick List)
- ✅ Complete authentication system
- ✅ Production-ready build configuration

Your React Native WMS mobile app should now install and run successfully!