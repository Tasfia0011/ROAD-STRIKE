import cv2
import numpy as np
import datetime


def capture_thermal_analysis():
    # 1. Initialize Camera
    cap = cv2.VideoCapture(0)

    if not cap.isisOpened():
        print("Error: Could not access camera.")
        return

    print("Press 'q' to capture and analyze, or 'esc' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 2. Convert to Grayscale (Intensity Map)
        # We treat brightness as a proxy for 'heat' for the simulation
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 3. Apply Heatmap Effect
        # COLORMAP_JET or COLORMAP_INFERNO mimics thermal aesthetics
        thermal_sim = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        # Display the live simulation
        cv2.imshow('Thermal Simulation Mode', thermal_sim)

        key = cv2.waitKey(1)
        if key == ord('q'):
            # Capture the current frame for analysis
            analyze_frame(gray, thermal_sim)
            break
        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


def analyze_frame(intensity_map, visual_frame):
    # 4. Data Extraction
    avg_intensity = np.mean(intensity_map)
    max_intensity = np.max(intensity_map)
    min_intensity = np.min(intensity_map)

    # Calculate "Heat" Distribution (Histogram)
    hist = cv2.calcHist([intensity_map], [0], None, [5], [0, 256])

    # 5. Generate Report
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n--- THERMAL SIMULATION REPORT ---")
    print(f"Timestamp: {timestamp}")
    print(f"Global Intensity Average: {avg_intensity:.2f}/255")
    print(f"Peak 'Heat' Signature: {max_intensity}")
    print("---------------------------------")
    print("Distribution Analysis:")
    zones = ["Cold", "Cool", "Neutral", "Warm", "Hot"]
    for i, count in enumerate(hist):
        percentage = (count[0] / intensity_map.size) * 100
        print(f"Zone {zones[i]}: {percentage:.2f}% of frame")

    # Save the result
    cv2.imwrite("thermal_capture.jpg", visual_frame)
    print("\nAnalysis Complete. Image saved as 'thermal_capture.jpg'.")


if __name__ == "__main__":
    capture_thermal_analysis()