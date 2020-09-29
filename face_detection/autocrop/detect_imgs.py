import cv2
import time

from fd_config import define_img_size
define_img_size(640)
from mb_tiny_RFB_fd import create_Mb_Tiny_RFB_fd, create_Mb_Tiny_RFB_fd_predictor


result_path = "./detect_imgs_results"
label_path = "./models/voc-model-labels.txt"
class_names = [name.strip() for name in open(label_path).readlines()]
model_path = "models/pretrained/version-RFB-640.pth"
net = create_Mb_Tiny_RFB_fd(len(class_names), is_test=True, device="cpu")
predictor = create_Mb_Tiny_RFB_fd_predictor(net, candidate_size=1500, device="cpu")
net.load(model_path)

orig_image = cv2.imread("jan.jpg")

image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
boxes, labels, probs = predictor.predict(image, 1500 / 2, 0.6)
print(boxes)
if len(boxes) == 0:
    print("gay")
box = boxes[0, :]
crop = orig_image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
cv2.imwrite("jan_crop.jpg", crop)


