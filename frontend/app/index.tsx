import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { useState, useEffect, useRef } from 'react';
import { Button, StyleSheet, Text, View } from 'react-native';
import * as FileSystem from 'expo-file-system';

export default function Index() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [isRecording, setIsRecording] = useState(false);
  const localFolderPath = FileSystem.documentDirectory + 'captured_frames/';
  useEffect(() => {
    async function createDirectory() {
      const dirInfo = await FileSystem.getInfoAsync(localFolderPath);
      if (!dirInfo.exists) {
        await FileSystem.makeDirectoryAsync(localFolderPath, { intermediates: true });
        console.log(`Created directory at: ${localFolderPath}`);
      }
    }
    createDirectory();
  }, []);

  useEffect(() => {
    let interval: string | number | NodeJS.Timeout | undefined;
    if (isRecording) {
      interval = setInterval(async () => {
        if (cameraRef.current) {
          try {
            const photo = await cameraRef.current.takePictureAsync({
              base64: false,
              skipProcessing: true,
            });
            if (photo) {
              const fileUri = `${localFolderPath}frame_${Date.now()}.jpg`;
              await FileSystem.moveAsync({
                from: photo.uri,
                to: fileUri,
              });
              console.log(`Saved frame to: ${fileUri}`);
            }
          } catch (error) {
            console.error('Error capturing frame:', error);
          }
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant Permission" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera} facing={facing} onCameraReady={() => setIsRecording((prev) => !prev)}>
        {/* <View style={styles.buttonContainer}>
          <Button
            title={isRecording ? 'Stop Capturing' : 'Start Capturing'}
            onPress={() => setIsRecording((prev) => !prev)}
          />
        </View> */}
      </CameraView>
    </View >
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 50,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
});
