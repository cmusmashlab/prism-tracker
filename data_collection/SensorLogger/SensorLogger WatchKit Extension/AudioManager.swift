//
//  AudioManager.swift
//  SensorLogger WatchKit Extension
//
//  Created by Vicky Liu + Riku Arakawa  on 2/28/22.
//

import WatchKit
import AVFoundation
import CloudKit

class AudioManager:  WKInterfaceController, AVAudioRecorderDelegate{
    
    var recordingSession: AVAudioSession!
    var recorder: AVAudioRecorder?
    var audioURL = FileManager.default.getDocumentsDirectory()
    var timeURL = FileManager.default.getDocumentsDirectory()
    var audioPlayer: AVAudioPlayer!
    var timeText = ""
    
    func startRecording(participantID pID: String, sessionID sID: String) {
        audioURL = audioURL.appendingPathComponent("\(pID)-\(sID).wav")
        timeURL = timeURL.appendingPathComponent("\(pID)-\(sID)-audiotime.txt")
        
        let settings = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 32000,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        do {
            recorder = try AVAudioRecorder(url: audioURL, settings: settings)
            recorder?.delegate = self
            recorder?.record()
            timeText += "Start time: \(NSDate().timeIntervalSince1970) \n"
            print ("Start recording")
        } catch {
            
            print ("Recording failed")
        }
    }
    
    func endRecording() {
        recorder?.stop()
        timeText += "End time: \(NSDate().timeIntervalSince1970)"
        print ("End recording")
        do {
            try timeText.write(to: timeURL, atomically: true, encoding: .utf8)
        } catch {
            print("Error", error)
            return
        }
        recorder = nil
    }
    
    func setupView() {
        recordingSession = AVAudioSession.sharedInstance()
        
        do {
            try recordingSession.setCategory(.playAndRecord, mode: .default)
            try recordingSession.setActive(true)
            recordingSession.requestRecordPermission() { [unowned self] allowed in
                DispatchQueue.main.async {
                    if allowed {
                    } else {
                        print("Failed to record")
                    }
                }
            }
        } catch {
            print("Failed to record")
        }
    }
    
}

