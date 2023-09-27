import cv2 as cv
import numpy as np
import mediapipe as mp
import pyautogui

cap = cv.VideoCapture(0)

pyautogui.FAILSAFE = False

# Pontos dos cantos do rosto que serão usados para detectar a inclinação da cabeça
left_face = [127]
right_face = [356]
top_face = [10]
bottom_face = [152]

# Pontos dos olhos que serão usados para detectar a direção do olhar
left_eye = [362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398]
right_eye= [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246]

left_iris = [474,475,476,477]
right_iris = [469,470,471,472] 

upper_lid = [159, 145]
lower_lid = [386, 380]

# Calcular centro do rosto
def face_center(points):
    x_vals = [point[0] for point in points]
    y_vals = [point[1] for point in points]
    center_x = sum(x_vals) / len(points)
    center_y = sum(y_vals) / len(points)
    return center_x, center_y

# Função modificada para classificar a direção baseada na inclinação da cabeça
def classify_head_direction(face_center, current_point, threshold_sides=6, threshold_updown=8):
    dx = current_point[0] - face_center[0]
    dy = face_center[1] - current_point[1]

    if abs(dx) < threshold_sides and abs(dy) < threshold_sides:
        return None

    if dx < -threshold_sides and dy < -threshold_sides:
        return "baixo esquerda"
    elif dx > threshold_sides and dy < -threshold_sides:
        return "baixo direita"
    elif dx < -threshold_sides and dy > threshold_sides:
        return "cima esquerda"
    elif dx > threshold_sides and dy > threshold_sides:
        return "cima direita"
    elif dx < -threshold_sides:
        return "esquerda"
    elif dx > threshold_sides:
        return "direita"
    elif dy < -threshold_updown:
        return "baixo"
    elif dy > threshold_updown:
        return "cima"

def move_mouse(direction):
    if not direction:
        return
    if direction == "esquerda":
        pyautogui.move(-20, 0)
    elif direction == "direita":
        pyautogui.move(20, 0)
    elif direction == "cima":
        pyautogui.move(0, -30)
    elif direction == "baixo":
        pyautogui.move(0, 30)
    elif direction == "cima esquerda":
        pyautogui.move(-10, -10)
    elif direction == "cima direita":
        pyautogui.move(10, -10)
    elif direction == "baixo esquerda":
        pyautogui.move(-10, 10)
    else: # baixo direita
        pyautogui.move(10, 10)

with mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as face_mesh:

    initial_face_center = None

    blink_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        frame = cv.flip(frame, 1)
        results = face_mesh.process(frame)
        img_h, img_w = frame.shape[:2]

        if results.multi_face_landmarks:
            mesh_points = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int) for p in results.multi_face_landmarks[0].landmark])
            landmarks = results.multi_face_landmarks[0].landmark

            # Obter pontos laterais do rosto
            left_point = mesh_points[left_face][0]
            right_point = mesh_points[right_face][0]
            top_point = mesh_points[top_face][0]
            bottom_point = mesh_points[bottom_face][0]
            right_eye_point = mesh_points[right_eye][0]
            left_eye_point = mesh_points[left_eye][0]

            # Draw iris landmarks
            (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[left_iris])
            (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[right_iris])

            left_iris_point = np.array([l_cx, l_cy], dtype=np.int32)
            right_iris_point = np.array([r_cx, r_cy], dtype=np.int32)

            cv.circle(frame, left_iris_point, int(l_radius), (255, 0, 255), 1, cv.LINE_AA)
            cv.circle(frame, right_iris_point, int(r_radius), (255, 0, 255), 1, cv.LINE_AA)

            # Desenhar pontos laterais do rosto
            cv.circle(frame, tuple(left_point), 5, (0, 255, 255), 1, cv.LINE_AA)
            cv.circle(frame, tuple(right_point), 5, (0, 255, 255), 1, cv.LINE_AA)
            cv.circle(frame, tuple(top_point), 5, (0, 0, 255), 1, cv.LINE_AA)
            cv.circle(frame, tuple(bottom_point), 5, (0, 0, 255), 1, cv.LINE_AA)

            # Calcular centro do rosto
            current_face_center = face_center([
                left_point, 
                right_point, 
                top_point, 
                bottom_point,
                ])

            # Definir centro inicial do rosto, se ainda não estiver definido
            if initial_face_center is None:
                initial_face_center = current_face_center

            # Desenhar centro do rosto
            cv.circle(frame, (int(current_face_center[0]), int(current_face_center[1])), 5, (255, 0, 0), -1, cv.LINE_AA)

            # Classificar direção baseado no movimento da cabeça
            direction = classify_head_direction(initial_face_center, current_face_center)

            move_mouse(direction)

            left = [landmarks[145], landmarks[159]]
            if (left[0].y - left[1].y) < 0.004:
                pyautogui.click()
                pyautogui.sleep(1)

        cv.imshow('Face Mesh', frame)

        if cv.waitKey(1) == ord('q'):
            break
