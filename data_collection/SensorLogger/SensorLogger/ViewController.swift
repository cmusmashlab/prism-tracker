//
//  ViewController.swift
//  SensorLogger
//
//  Created by Vicky Liu + Riku Arakawa  on 2/25/22.
//

import UIKit
import WatchConnectivity

class ViewController: UIViewController {
    
    @IBOutlet weak var watchStatusLabel: UILabel!
    @IBOutlet weak var participantIDField: UITextField!
    @IBOutlet weak var sessionIDField: UITextField!
    @IBOutlet weak var pairButton: UIButton!
    @IBOutlet weak var startButton: UIButton!
    @IBOutlet weak var stopButton: UIButton!
    
    var participantText = ""
    var sessionText = ""
    var savedText = ""
    var watchCnt = 0
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
        if (WCSession.isSupported()) {
            let session = WCSession.default
            session.delegate = self
            session.activate()
        }
        
        self.hideKeyboardWhenTapped()
        participantIDField.delegate = self
        sessionIDField.delegate = self
        
        watchStatusLabel.text = "Watch should be paired."
        pairButton.isEnabled = true
        startButton.isEnabled = false
        stopButton.isEnabled = false
    }
    
    @IBAction func pairWatch() {
        
        print("status")
        print(WCSession.default.isWatchAppInstalled)
        print(WCSession.default.isPaired)
        print(WCSession.default.isReachable)
        
        if (WCSession.default.isReachable) && (participantIDField.text != "") && (sessionIDField.text != "") {
            do {
                watchCnt = 0
                participantText = participantIDField.text as String? ?? ""
                sessionText = sessionIDField.text as String? ?? ""
                
                try WCSession.default.updateApplicationContext(["participantID": participantText, "sessionID": sessionText])
                print ("pID and sID transferred")
                
                watchStatusLabel.text = "Watch is paired. Ready to start."
                pairButton.isEnabled = false
                startButton.isEnabled = true
                stopButton.isEnabled = false
            }
            catch {
                print(error)
            }
        } else if (participantIDField.text == "") || (sessionIDField.text == "") {
            watchStatusLabel.text = "Participant field or session field is empty"
        } else {
            watchStatusLabel.text = "Watch is not reachable"
        }
    }
    
    private func startingOperations() {
        
        DispatchQueue.main.async {
            self.watchStatusLabel.text = "Recording"
            self.pairButton.isEnabled = false
            self.startButton.isEnabled = false
            self.stopButton.isEnabled = true
        }
    }
    
    @IBAction func startWatchMotion(_ sender: Any) {
        
        
        if (WCSession.default.isReachable) {
            do {
                try WCSession.default.updateApplicationContext(["command": "start"])
                startingOperations()
            }
            catch {
                print(error)
            }
        } else {
            watchStatusLabel.text = "Watch is not reachable"
        }
    }
    
    private func stoppingOperations() {
        
        do {
            try savedText.write(
                to: FileManager.default.getDocumentsDirectory().appendingPathComponent("\(participantText)-\(sessionText)-realtime.txt"),
                atomically: true,
                encoding: .utf8
            )
            DispatchQueue.main.async {
                self.watchStatusLabel.text = "Saved motion data"
                self.pairButton.isEnabled = false
                self.startButton.isEnabled = false
                self.stopButton.isEnabled = false
            }
        } catch {
            print("Error", error)
            DispatchQueue.main.async {
                self.watchStatusLabel.text = "Fail to save motion data"
            }
        }
    }
    
    @IBAction func stopWatchMotion(_ sender: Any) {
        
        if (WCSession.default.isReachable) {
            do {
                try WCSession.default.updateApplicationContext(["command": "stop"])
                stoppingOperations()
            }
            catch {
                print(error)
            }
        } else {
            watchStatusLabel.text = "Watch is not reachable"
        }
        
    }
}

extension UIViewController {
    
    @objc func hideKeyboardWhenTapped() {
        let tap: UITapGestureRecognizer = UITapGestureRecognizer(target: self, action: #selector(UIViewController.dismissKeyboard))
        tap.cancelsTouchesInView = false
        view.addGestureRecognizer(tap)
    }
    
    @objc func dismissKeyboard() {
        view.endEditing(true)
    }
}

extension ViewController: UITextFieldDelegate {
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        textField.resignFirstResponder()
        return true
    }
}

extension ViewController: WCSessionDelegate {
    
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        
    }
    
    func session(_ session: WCSession, didReceive file: WCSessionFile) {
        var dataURL = FileManager.default.getDocumentsDirectory()
        if (file.fileURL.absoluteString.contains(".txt")) {
            dataURL = dataURL.appendingPathComponent("\(participantText)-\(sessionText)-audiotime.txt")
        } else if (file.fileURL.absoluteString.contains(".wav")) {
            dataURL = dataURL.appendingPathComponent("\(participantText)-\(sessionText).wav")
        }
        do {
            try FileManager.default.moveItem(at: file.fileURL, to: dataURL)
            // logging to know if the audio data is saved
            DispatchQueue.main.async {
                self.watchStatusLabel.text = "Saved Audio Files [STUDY END]"
            }
        }
        catch let error{
            print (error)
        }
    }
    
    func session(_ session: WCSession, didReceiveMessage message: [String : Any] = [:]) {
        if let motionData = message["motionData"] as? String {
            print ("Received motion data")
            savedText += motionData
            
            // real-time logging on the phone
            watchCnt += 1
            if watchCnt % 50 == 0 {
                DispatchQueue.main.async {
                    self.watchStatusLabel.text = "\(self.watchCnt) data"
                }
            }
        }
        
        // logging to know if the motion data is saved
        if let status = message["command"] as? String {
            if status == "start" {
                startingOperations()
            } else if status == "stop" {
                stoppingOperations()
            }
        }
    }
    
    func sessionDidBecomeInactive(_ session: WCSession) {
        
    }
    
    func sessionDidDeactivate(_ session: WCSession) {
        
    }
}
