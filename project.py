# AI-Powered College Attendance Tracker using Face Recognition
# Dependencies: pip install opencv-python numpy mysql-connector-python pillow python-dotenv

import cv2
import numpy as np
import mysql.connector
from datetime import datetime
import os
import pickle
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AttendanceTracker: 
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'attendance_db')
        }
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.known_faces = []
        self.known_names = []
        self.students_data = {}
        
        # Create directories if they don't exist
        os.makedirs('student_images', exist_ok=True)
        os.makedirs('models', exist_ok=True)
        
        self.setup_database()
        self.load_trained_model()
        
    def setup_database(self):
        """Initialize MySQL database and tables"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    phone VARCHAR(15),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    status ENUM('Present', 'Absent') DEFAULT 'Present',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    UNIQUE KEY unique_attendance (student_id, date)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("Database setup completed successfully!")
            
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
    
    def add_student(self, student_id, name, email="", phone=""):
        """Add a new student to the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO students (student_id, name, email, phone)
                VALUES (%s, %s, %s, %s)
            ''', (student_id, name, email, phone))
            
            conn.commit()
            conn.close()
            return True
            
        except mysql.connector.Error as err:
            print(f"Error adding student: {err}")
            return False
    
    def capture_student_images(self, student_id, name, num_images=20):
        """Capture images for face recognition training"""
        cap = cv2.VideoCapture(0)
        count = 0
        
        print(f"Capturing images for {name}. Press 'q' to quit early.")
        
        while count < num_images:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BAYER_BG2RGB)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                face_roi = gray[y:y+h, x:x+w]
                
                # Save the face image
                img_path = f'student_images/{student_id}_{count}.jpg'
                cv2.imwrite(img_path, face_roi)
                count += 1
                
                cv2.putText(frame, f'Images captured: {count}/{num_images}', 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Capturing Images', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"Captured {count} images for {name}")
        return count > 0
    
    def train_model(self):
        """Train the face recognition model"""
        faces = []
        labels = []
        student_ids = []
        
        # Load all student images
        for filename in os.listdir('student_images'):
            if filename.endswith('.jpg'):
                student_id = filename.split('_')[0]
                
                # Load student info from database
                conn = mysql.connector.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM students WHERE student_id = %s', (student_id,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    name = result[0]
                    
                    # Load and process the image
                    img_path = os.path.join('student_images', filename)
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    
                    if img is not None:
                        faces.append(img)
                        
                        # Create unique label for each student
                        if student_id not in student_ids:
                            student_ids.append(student_id)
                            self.students_data[len(student_ids)-1] = {'id': student_id, 'name': name}
                        
                        labels.append(student_ids.index(student_id))
        
        if len(faces) > 0:
            # Train the recognizer
            self.recognizer.train(faces, np.array(labels))
            
            # Save the trained model
            self.recognizer.save('models/face_recognizer.yml')
            
            # Save student data
            with open('models/students_data.pkl', 'wb') as f:
                pickle.dump(self.students_data, f)
            
            print("Model trained successfully!")
            return True
        else:
            print("No training data found!")
            return False
    
    def load_trained_model(self):
        """Load the trained face recognition model"""
        try:
            if os.path.exists('models/face_recognizer.yml'):
                self.recognizer.read('models/face_recognizer.yml')
                
                with open('models/students_data.pkl', 'rb') as f:
                    self.students_data = pickle.load(f)
                
                print("Model loaded successfully!")
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        return False
    
    def mark_attendance(self, student_id):
        """Mark attendance for a student"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            
            # Check if attendance already marked today
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE student_id = %s AND date = %s
            ''', (student_id, current_date))
            
            if cursor.fetchone():
                conn.close()
                return False, "Attendance already marked today"
            
            # Mark attendance
            cursor.execute('''
                INSERT INTO attendance (student_id, date, time, status)
                VALUES (%s, %s, %s, 'Present')
            ''', (student_id, current_date, current_time))
            
            conn.commit()
            conn.close()
            return True, "Attendance marked successfully"
            
        except mysql.connector.Error as err:
            print(f"Error marking attendance: {err}")
            return False, str(err)
    
    def recognize_faces(self):
        """Real-time face recognition for attendance"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
             messagebox.showerror("Error", "Could not access camera!")
             return

            print("Starting face recognition. Press 'q' to quit.")
        
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
            
                # ...existing face recognition code...
            
                cv2.imshow('Attendance Tracker', frame)
            
                # Check for 'q' key or window close button
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty('Attendance Tracker', cv2.WND_PROP_VISIBLE) < 1:
                    break
        
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {e}")
        finally:
            # Ensure proper cleanup
            cap.release()
            cv2.destroyAllWindows()
            # Force close any remaining windows
            for i in range(4):
                cv2.waitKey(1)
    
    def get_attendance_report(self, date=None):
        """Generate attendance report"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT s.student_id, s.name, a.date, a.time, a.status
                    FROM students s
                    LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = %s
                    ORDER BY s.name
                ''', (date,))
            else:
                cursor.execute('''
                    SELECT s.student_id, s.name, a.date, a.time, a.status
                    FROM students s
                    LEFT JOIN attendance a ON s.student_id = a.student_id
                    ORDER BY s.name, a.date DESC
                ''')
            
            results = cursor.fetchall()
            conn.close()
            return results
            
        except mysql.connector.Error as err:
            print(f"Error generating report: {err}")
            return []

class AttendanceGUI:
    def __init__(self):
        self.tracker = AttendanceTracker()
        self.root = tk.Tk()
        self.root.title("AI-Powered Attendance Tracker")
        self.root.geometry("800x600")
        
        self.setup_gui()
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="AI-Powered College Attendance Tracker", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Student Registration Frame
        reg_frame = ttk.LabelFrame(main_frame, text="Student Registration", padding="10")
        reg_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(reg_frame, text="Student ID:").grid(row=0, column=0, sticky=tk.W)
        self.student_id_entry = ttk.Entry(reg_frame, width=20)
        self.student_id_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(reg_frame, text="Name:").grid(row=1, column=0, sticky=tk.W)
        self.name_entry = ttk.Entry(reg_frame, width=20)
        self.name_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(reg_frame, text="Email:").grid(row=2, column=0, sticky=tk.W)
        self.email_entry = ttk.Entry(reg_frame, width=20)
        self.email_entry.grid(row=2, column=1, padx=5)
        
        ttk.Button(reg_frame, text="Register Student", 
                  command=self.register_student).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Control Buttons Frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(control_frame, text="Train Model", 
                  command=self.train_model).grid(row=0, column=0, padx=5)
        
        ttk.Button(control_frame, text="Start Attendance", 
                  command=self.start_attendance).grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="View Report", 
                  command=self.view_report).grid(row=0, column=2, padx=5)
        
        # Report Frame
        report_frame = ttk.LabelFrame(main_frame, text="Attendance Report", padding="10")
        report_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Treeview for displaying reports
        self.tree = ttk.Treeview(report_frame, columns=('ID', 'Name', 'Date', 'Time', 'Status'), 
                                show='headings', height=10)
        
        self.tree.heading('ID', text='Student ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Time', text='Time')
        self.tree.heading('Status', text='Status')
        
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        report_frame.columnconfigure(0, weight=1)
        report_frame.rowconfigure(0, weight=1)
    
    def register_student(self):
        student_id = self.student_id_entry.get().strip()
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        
        if not student_id or not name:
            messagebox.showerror("Error", "Student ID and Name are required!")
            return
        
        # Add student to database
        if self.tracker.add_student(student_id, name, email):
            # Capture images for training
            if messagebox.askyesno("Capture Images", 
                                 f"Register {name} successfully! Do you want to capture images for face recognition?"):
                self.tracker.capture_student_images(student_id, name)
            
            # Clear entries
            self.student_id_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            
            messagebox.showinfo("Success", "Student registered successfully!")
        else:
            messagebox.showerror("Error", "Failed to register student!")
    
    def train_model(self):
        if self.tracker.train_model():
            messagebox.showinfo("Success", "Model trained successfully!")
        else:
            messagebox.showerror("Error", "Failed to train model!")
    
    def start_attendance(self):
        self.tracker.recognize_faces()
    
    def view_report(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get today's report
        today = datetime.now().date()
        report = self.tracker.get_attendance_report(today)
        
        for row in report:
            student_id, name, date, time, status = row
            if date is None:
                date = "N/A"
                time = "N/A"
                status = "Absent"
            
            self.tree.insert('', 'end', values=(student_id, name, date, time, status))
    
    def run(self):
        self.root.mainloop()

# Usage instructions and setup
if __name__ == "__main__":
    print("AI-Powered College Attendance Tracker")
    print("=====================================")
    print("\nSetup Instructions:")
    print("1. Install required packages:")
    print("   pip install opencv-python numpy mysql-connector-python pillow python-dotenv")
    print("2. Create a .env file in the project root with:")
    print("   DB_HOST=localhost")
    print("   DB_USER=root")
    print("   DB_PASSWORD=your_password")
    print("   DB_NAME=attendance_db")
    print("3. Install MySQL and create a database named 'attendance_db'")
    print("4. Run the application")
    print("\nFeatures:")
    print("- Face recognition-based attendance")
    print("- Student registration with image capture")
    print("- Real-time attendance marking")
    print("- Attendance reports")
    print("- User-friendly GUI")

    # Uncomment the following lines to run the GUI
    app = AttendanceGUI()
    app.run()
