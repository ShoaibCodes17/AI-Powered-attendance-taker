# AI-Powered College Attendance Tracker

An intelligent attendance management system that uses face recognition technology to automatically mark student attendance in real-time. This application combines OpenCV for face detection, LBPH (Local Binary Patterns Histograms) for face recognition, and MySQL for data persistence.

## Features

✨ **Key Capabilities:**
- 🎯 **Face Recognition-Based Attendance**: Automatic attendance marking using real-time face detection
- 📋 **Student Registration**: Easy student onboarding with profile information
- 📸 **Image Capture**: Automated collection of face images for model training
- 🧠 **Model Training**: LBPH face recognizer trained on student face images
- 📊 **Attendance Reports**: Generate and view attendance records with filtering options
- 🖥️ **User-Friendly GUI**: Intuitive Tkinter-based interface for all operations
- 💾 **Database Integration**: MySQL backend for secure data storage
- 🔒 **Secure Configuration**: Environment variables for sensitive database credentials

## Technology Stack

- **Language**: Python 3.x
- **Face Detection**: OpenCV (Haar Cascade Classifier)
- **Face Recognition**: OpenCV LBPH Face Recognizer
- **GUI Framework**: Tkinter
- **Database**: MySQL with mysql-connector-python
- **Image Processing**: PIL/Pillow, NumPy
- **Configuration**: Python-dotenv

## Installation

### Prerequisites
- Python 3.6 or higher
- MySQL Server installed and running
- A webcam for image capture

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ShoaibCodes17/AI-Powered-attendance-taker.git
   cd AI-Powered-attendance-taker
   ```

2. **Install required Python packages**
   ```bash
   pip install opencv-python numpy mysql-connector-python pillow python-dotenv
   ```

3. **Create a MySQL database**
   ```sql
   CREATE DATABASE attendance_db;
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root directory:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=attendance_db
   ```

5. **Run the application**
   ```bash
   python project.py
   ```

## Usage Guide

### 1. Student Registration
1. Open the application
2. Enter Student ID, Name, and Email in the "Student Registration" section
3. Click "Register Student"
4. When prompted, click "Yes" to capture face images
5. Position your face clearly in front of the camera
6. The system will capture 20 images automatically

### 2. Train the Model
1. After registering multiple students and capturing their images
2. Click the "Train Model" button in the Controls section
3. Wait for the model to train (processes all captured images)
4. A success message confirms training completion

### 3. Start Attendance
1. Click "Start Attendance" to begin face recognition
2. Students should present their faces to the camera
3. Detected faces are recognized and attendance is automatically marked
4. Press 'q' to stop the recognition process

### 4. View Reports
1. Click "View Report" to display today's attendance
2. The report shows all students with their attendance status
3. Absent students display as "Absent"

## Project Structure

```
AI-Powered-attendance-taker/
├── project.py                 # Main application file
├── .env                       # Environment configuration (create this)
├── student_images/            # Auto-created directory for student photos
├── models/                    # Auto-created directory for trained models
│   ├── face_recognizer.yml   # Trained LBPH model
│   └── students_data.pkl     # Student metadata
└── README.md                  # This file
```

## Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    status ENUM('Present', 'Absent') DEFAULT 'Present',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    UNIQUE KEY unique_attendance (student_id, date)
);
```

## Key Classes and Methods

### AttendanceTracker Class
Main class handling all core functionality:

- **`__init__()`**: Initializes database, face cascade, and recognizer
- **`setup_database()`**: Creates required MySQL tables
- **`add_student()`**: Registers a new student
- **`capture_student_images()`**: Captures 20 images per student for training
- **`train_model()`**: Trains the LBPH face recognizer
- **`load_trained_model()`**: Loads previously trained model
- **`recognize_faces()`**: Real-time face recognition and attendance marking
- **`mark_attendance()`**: Records attendance in database
- **`get_attendance_report()`**: Retrieves attendance records

### AttendanceGUI Class
Handles the user interface:

- **`setup_gui()`**: Creates all GUI components
- **`register_student()`**: GUI handler for student registration
- **`train_model()`**: GUI handler for model training
- **`start_attendance()`**: GUI handler for attendance marking
- **`view_report()`**: GUI handler for displaying reports
- **`run()`**: Starts the Tkinter main loop

## Important Notes

⚠️ **Considerations:**
- Ensure proper lighting conditions for optimal face recognition
- Capture diverse face images (different angles, distances) for better accuracy
- Each student can only be marked present once per day
- The model file needs retraining after adding new students
- Ensure MySQL server is running before launching the application
- The `.env` file should never be committed to version control

## Troubleshooting

**Issue**: "Could not access camera!"
- Solution: Check camera permissions and ensure no other app is using the camera

**Issue**: Database connection errors
- Solution: Verify MySQL is running and `.env` credentials are correct

**Issue**: Model training fails
- Solution: Ensure student images exist in the `student_images/` folder

**Issue**: Face recognition not working
- Solution: Retrain the model after capturing fresh images with better lighting

## Future Enhancements

- 🔐 User authentication and role-based access
- 📱 Mobile app integration
- 🌐 Web-based interface
- 👥 Multi-camera support
- 📈 Advanced attendance analytics
- 🔔 Automated notifications
- 🗣️ Multiple language support

## License

This project is open source and available under the MIT License.

## Author

**ShoaibCodes17**

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For issues, questions, or suggestions, please create an issue on the GitHub repository.

---

**Note**: This application requires a MySQL database and a webcam. Ensure all dependencies are properly installed before running the application.
