import { CameraView, CameraType } from 'expo-camera';
import { useState, useEffect, useRef } from 'react';
import { View } from 'react-native';
import * as Haptics from 'expo-haptics';
import 'react-native-get-random-values';
import { v4 as uuidv4 } from 'uuid';

export default function Index() {
  const [facing, setFacing] = useState<CameraType>('back');
  const cameraRef = useRef<CameraView>(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    let interval: string | number | NodeJS.Timeout | undefined;
    if (isRecording) {
      interval = setInterval(async () => {
        if (cameraRef.current) {
          try {
            const uniqueId = uuidv4();
            const photo = await cameraRef.current.takePictureAsync({ quality: 0.5, base64: true, skipProcessing: true });
            if (photo && photo.base64) {
              const isHazard = await checkForHazard(photo.base64, uniqueId);
              if (isHazard) {
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
              }
            }
          } catch (error) {
            console.error('Error taking pic:', error);
          }
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  async function checkForHazard(imageBase64: string, uniqueId: string) {
    try {
      const URL = "SOMEHTING HERE"
      const response = await fetch(URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain',
        },
        body: `${uniqueId}|${imageBase64}`,
      });
      const data = await response.json();
      return data.is_hazard;
    } catch (error) {
      console.error('Error sending image to backend:', error);
      return false;
    }
  }
  return (
    <View style={{ flex: 1, justifyContent: 'center'}}>
      <CameraView flash='off' ref={cameraRef} style={{ flex: 1 }} facing={facing} onCameraReady={() => setIsRecording((prev) => !prev)} />
    </View >
  );
}
