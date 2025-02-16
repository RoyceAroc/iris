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
  const ws = useRef<WebSocket | null>(null);
  const [captions, setCaptions] = useState<Record<string, string>>({});

  useEffect(() => {
    ws.current = new WebSocket("ws://127.0.0.1:9001");
    ws.current.onopen = () => {
      console.log("Connected to WebSocket server");
    };
    ws.current.onmessage = (event) => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const message = event.data;
      console.log("Received from WebSocket:", message);
      const [uid, token] = message.split("|");
      if (token.trim() === "<end>") {
        console.log(`Final caption received for UID ${uid}: ${captions[uid]}`);
        return;
      }
      setCaptions((prevCaptions: { [x: string]: string; }) => ({
        ...prevCaptions,
        [uid]: prevCaptions[uid] ? prevCaptions[uid] + " " + token : token,
      }));
    };
    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
    ws.current.onclose = () => {
      console.log("WebSocket connection closed");
    };
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    let interval: string | number | NodeJS.Timeout | undefined;
    if (isRecording) {
      interval = setInterval(async () => {
        if (cameraRef.current) {
          try {
            const uniqueId = uuidv4();
            const photo = await cameraRef.current.takePictureAsync({ quality: 0.5, base64: true, skipProcessing: true });
            if (photo && photo.base64) {
              const dataString = `${uniqueId}|${photo.base64}`;
              if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.send(dataString);
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

  return (
    <View style={{ flex: 1, justifyContent: 'center' }}>
      <CameraView flash='off' ref={cameraRef} style={{ flex: 1 }} facing={facing} onCameraReady={() => setIsRecording((prev) => !prev)} />
    </View >
  );
}
