# Khanfar TX v2
*Developed by Khanfar Systems*

A powerful remote control GUI for rpitx, enabling wireless RF transmission control through SSH.

## Features
- Remote SSH connection to Raspberry Pi
- Frequency control (5 KHz to 1500 MHz)
- Multiple transmission modes supported:
  - Tune (Carrier Signal)
  - Chirp (Moving Carrier)
  - Spectrum (JPG Painting)
  - FM RDS (Broadcast)
  - NFM (Narrow Band FM)
  - SSB (Upper Side Band)
  - AM (Amplitude Modulation)
  - FreeDV (Digital Voice)
  - SSTV (Slow Scan TV)
  - POCSAG (Pager Messages)
  - Opera (Special Morse)
  - RTTY (Radioteletype)

## Requirements
- Python 3.6 or higher
- Required Python packages:
  ```sh
  pip install paramiko
  pip install tkinter
  ```
- Rpitx installed on your Raspberry Pi
- SSH access to your Raspberry Pi

## Quick Start Guide

### 1. Installation
1. Ensure rpitx is installed on your Raspberry Pi
2. Install required Python packages:
   ```sh
   pip install -r requirements.txt
   ```

### 2. Starting the GUI
```sh
python rpitx_remote_gui.py
```

### 3. Connection Setup
1. Enter your Raspberry Pi's details:
   - Host: IP address (e.g., 192.168.1.100)
   - Username: SSH username
   - Password: SSH password
   - Rpitx Path: Path to rpitx (default: /home/username/rpitx)

### 4. Using the GUI

#### Basic Operations
1. Set your desired frequency in MHz
2. Choose a transmission mode
3. Monitor the status indicator
4. Use "Stop Transmission" when needed

#### Transmission Modes
- **Tune**: Simple carrier signal
- **Chirp**: Moving carrier signal
- **Spectrum**: Transmit images as RF
- **FM RDS**: FM broadcast with RDS
- **NFM**: Narrow band FM
- **SSB**: Upper side band modulation
- **AM**: Amplitude modulation
- **FreeDV**: Digital voice
- **SSTV**: Slow scan television
- **POCSAG**: Pager messages
- **Opera**: Special morse mode
- **RTTY**: Radioteletype

## Safety and Best Practices
- Always use appropriate RF filtering
- Follow local RF transmission regulations
- Monitor Raspberry Pi temperature
- Use emergency stop when needed
- Keep proper antenna length for frequency

## Troubleshooting
1. **Connection Issues**
   - Verify SSH access to Raspberry Pi
   - Check network connectivity
   - Confirm correct credentials

2. **Transmission Problems**
   - Verify rpitx installation
   - Check file permissions
   - Monitor GUI status messages

3. **File Upload Issues**
   - Ensure sufficient disk space
   - Verify write permissions
   - Check file format compatibility

## Support
For issues, feature requests, or contributions, please contact Khanfar Systems.

## License
This software is part of the rpitx project and follows its licensing terms.

---
*Khanfar TX v2 - Professional RF Control Solution*
*Copyright © 2024 Khanfar Systems. All rights reserved.*
