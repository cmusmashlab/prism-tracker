//
//  InterfaceController.swift
//  SensorLogger WatchKit Extension
//
//  Created by Vicky Liu + Riku Arakawa  on 2/25/22.
//

import WatchKit
import Foundation
import WatchConnectivity
import UIKit
import AVFoundation


class InterfaceController: WKInterfaceController {
    
    let motionManager = MotionManager()
    let audioManager = AudioManager()
    var url = FileManager.default.getDocumentsDirectory()
    var participantID = ""
    var sessionID = ""
    @IBOutlet weak var pIDLabel: WKInterfaceLabel!
    @IBOutlet weak var sIDLabel: WKInterfaceLabel!
    @IBOutlet weak var recordingLabel: WKInterfaceLabel!
    @IBOutlet weak var startButton: WKInterfaceButton!
    @IBOutlet weak var stopButton: WKInterfaceButton!
    @IBOutlet weak var shareButton: WKInterfaceButton!
    
    override func awake(withContext context: Any?) {
        // Configure interface objects here.
        audioManager.setupView()  // THIS IS CRITICAL for continuing the MOTION recording.
        recordingLabel.setText("Need Pairing from Phone")
        startButton.setEnabled(false)
        stopButton.setEnabled(false)
        shareButton.setEnabled(false)
    }
    
    override func willActivate() {
        // This method is called when watch view controller is about to be visible to user
        print("will activate!!!")
        if WCSession.isSupported() {
            let session = WCSession.default
            session.delegate = self
            session.activate()
            print("is reachable ", session.isReachable)
        }
    }
    
    private func start() {
        motionManager.startRecording(participantID: participantID, sessionID: sessionID)
        audioManager.startRecording(participantID: participantID, sessionID: sessionID)
        recordingLabel.setText("Recording")
        startButton.setEnabled(false)
        stopButton.setEnabled(true)
        shareButton.setEnabled(false)
    }
    
    private func stop() {
        motionManager.endRecording(participantID: participantID, sessionID: sessionID)
        audioManager.endRecording()
        recordingLabel.setText("Not Recording")
        startButton.setEnabled(false)
        stopButton.setEnabled(false)
        shareButton.setEnabled(true)
    }
    
    @IBAction func startButtonPressed() {
        try WCSession.default.sendMessage(["command": "start"], replyHandler: nil)
        start()
    }
    
    @IBAction func stopButtonPressed() {
        try WCSession.default.sendMessage(["command": "stop"], replyHandler: nil)
        stop()
    }
    
    @IBAction func shareButtonPressed() {
        recordingLabel.setText("Sharing")
        if (WCSession.default.isReachable) {
            WCSession.default.transferFile(url.appendingPathComponent("\(participantID)-\(sessionID).wav"), metadata: nil)
            WCSession.default.transferFile(url.appendingPathComponent("\(participantID)-\(sessionID)-audiotime.txt"), metadata: nil)
            print ("Sucessfully shared")
        }
        startButton.setEnabled(false)
        stopButton.setEnabled(false)
        shareButton.setEnabled(false)
    }
}

extension InterfaceController: WCSessionDelegate {
    
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        
    }
    
    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String : Any]) {
        
        if let command = applicationContext["command"] as? String {
            
            if command == "start" {
                start()
            } else if command == "stop" {
                stop()
            }
        } else {
            if let pID = applicationContext["participantID"] as? String {
                participantID = pID
                pIDLabel.setText(participantID)
            }
            
            if let sID = applicationContext["sessionID"] as? String {
                sessionID = sID
                sIDLabel.setText(sessionID)
            }
            
            if participantID != "" && sessionID != "" {
                startButton.setEnabled(true)
                stopButton.setEnabled(false)
                shareButton.setEnabled(false)
            }
        }
    }
}
