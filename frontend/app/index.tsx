import { CameraView, CameraType } from "expo-camera";
import { useState, useEffect, useRef } from "react";
import { View } from "react-native";
import { Audio } from "expo-av";
import * as Haptics from "expo-haptics";
import "react-native-get-random-values";
import { v4 as uuidv4 } from "uuid";
import * as Speech from "expo-speech";
import * as ImageManipulator from 'expo-image-manipulator';

function base64ToArrayBuffer(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

export default function Index() {
  const [facing, setFacing] = useState<CameraType>("back");
  const cameraRef = useRef<CameraView>(null);
  const [isRecording, setIsRecording] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const [captions, setCaptions] = useState<Record<string, string>>({});
  const visitedUIDs = useRef<Set<string>>(new Set());
  const speechQueue = useRef<string[]>([]);
  const isSpeaking = useRef<boolean>(false);

  useEffect(() => {
    ws.current = new WebSocket("ws://209.20.159.34:2222");
    ws.current.onopen = () => {
      console.log("Connected to WebSocket server");
    };
    ws.current.onmessage = (event) => {
      const message = event.data;
      const [uid, token] = message.split("|");

      if (!visitedUIDs.current.has(uid)) {
        visitedUIDs.current.add(uid);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }

      if (token.trim() == "<end>") {
        startSpeech(captions[uid]);
      }

      if (captions[uid]) {
        captions[uid] = captions[uid] + " " + token;
      } else {
        captions[uid] = token;
      }
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

  function startSpeech(text: string) {
    if (!text || isSpeaking.current) return;
    isSpeaking.current = true;
    Audio.setAudioModeAsync({
      playsInSilentModeIOS: true,
      allowsRecordingIOS: false,
      shouldDuckAndroid: true,
    });
    Speech.speak(text, {
      rate: 1.0,
      language: "en",
      onDone: () => {
        isSpeaking.current = false;
      },
      onError: () => {
        isSpeaking.current = false;
      },
    });
  }

  useEffect(() => {
    let interval: string | number | NodeJS.Timeout | undefined;
    if (isRecording) {
      interval = setInterval(async () => {
        if (cameraRef.current) {
          try {
            const uniqueId = uuidv4();
            const photo = await cameraRef.current.takePictureAsync({
              quality: 0.5,
              base64: true,
              skipProcessing: true,
              shutterSound: false,
            });
            if (photo && photo.base64) {
              const resizedPhoto = await ImageManipulator.manipulateAsync(
                photo.uri,
                [{ resize: { width: 128, height: 128 } }],
                { base64: true }
              );
              if (resizedPhoto && resizedPhoto.base64) {
                const imageBuffer = base64ToArrayBuffer(resizedPhoto.base64);
                const idBuffer = new TextEncoder().encode(uniqueId + "|");
                const combinedBuffer = new Uint8Array(
                  idBuffer.length + imageBuffer.byteLength
                );

                combinedBuffer.set(idBuffer, 0);
                combinedBuffer.set(new Uint8Array(imageBuffer), idBuffer.length);

                if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                  console.log("Sending binary data to WebSocket");
                  ws.current.send(combinedBuffer);
                }
              }
            }
          } catch (error) {
            console.error("Error taking pic:", error);
          }
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  return (
    <View style={{ flex: 1, justifyContent: "center" }}>
      <CameraView
        mute={true}
        animateShutter={false}
        flash="off"
        ref={cameraRef}
        style={{ flex: 1 }}
        facing={facing}
        onCameraReady={() => setIsRecording((prev) => !prev)}
      />
    </View>
  );
}