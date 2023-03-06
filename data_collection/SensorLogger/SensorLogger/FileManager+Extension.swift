//
//  FileManager.swift
//  SensorLogger WatchKit Extension
//
//  Created by Vicky Liu + Riku Arakawa on 2/28/22.
//

import Foundation

extension FileManager {
    func getDocumentsDirectory() -> URL {
        let paths = urls(for: .documentDirectory, in: .userDomainMask)
        return paths[0]
    }
}

