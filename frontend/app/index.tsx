import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { useState, useEffect, useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import * as FileSystem from 'expo-file-system';
import * as Haptics from 'expo-haptics';

export default function Index() {
  const [facing, setFacing] = useState<CameraType>('back');
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
            const photo = await cameraRef.current.takePictureAsync({ base64: false });
            if (photo) {
              const fileUri = `${localFolderPath}frame_${Date.now()}.jpg`;
              await FileSystem.moveAsync({
                from: photo.uri,
                to: fileUri,
              });
              console.log(`Saved frame to: ${fileUri}`);
              const isHazard = await checkForHazard(fileUri);
              if (isHazard) {
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
              }
            }
          } catch (error) {
            console.error('Error capturing frame:', error);
          }
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  function createFormData(imageUri: any) {
    const formData = new FormData();
    const file = {
      uri: imageUri,
      name: `frame_${Date.now()}.jpg`,
      type: 'image/jpg',
    };
    formData.append('image', file as any);
    return formData;
  }

  async function checkForHazard(imageUri: any) {
    try {
      const URL = "SOMEHTING HERE"
      const response = await fetch(URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        body: createFormData(imageUri),
      });
      const data = await response.json();
      return data.is_hazard;
    } catch (error) {
      console.error('Error sending image to backend:', error);
      return false;
    }
  }
  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera} facing={facing} onCameraReady={() => setIsRecording((prev) => !prev)}>
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
