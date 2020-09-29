import matplotlib
import os
import sys
import time
from pathlib import Path
import yaml
from tqdm import tqdm
import imageio
import numpy as np
import face_alignment
from skimage.transform import resize
from skimage import img_as_ubyte
import torch
from sync_batchnorm import DataParallelWithCallback
from modules.generator import OcclusionAwareGenerator
from modules.keypoint_detector import KPDetector
from animate import normalize_kp
from scipy.spatial import ConvexHull
import subprocess

matplotlib.use('Agg')


class Fake:
    def __init__(self):
        config = os.path.join("files", "vox-256.yaml")
        checkpoint = os.path.join("files", "vox-cpk.pth.tar")
        self.generator, self.kp_detector = self.load_checkpoints(config_path=config, checkpoint_path=checkpoint)

    def load_checkpoints(self, config_path, checkpoint_path, cpu=False):
        with open(config_path) as f:
            config = yaml.load(f)

        generator = OcclusionAwareGenerator(**config['model_params']['generator_params'],
                                            **config['model_params']['common_params'])
        if not cpu:
            generator.cuda()

        kp_detector = KPDetector(**config['model_params']['kp_detector_params'],
                                 **config['model_params']['common_params'])
        if not cpu:
            kp_detector.cuda()

        if cpu:
            checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
        else:
            checkpoint = torch.load(checkpoint_path)

        generator.load_state_dict(checkpoint['generator'])
        kp_detector.load_state_dict(checkpoint['kp_detector'])

        if not cpu:
            generator = DataParallelWithCallback(generator)
            kp_detector = DataParallelWithCallback(kp_detector)

        generator.eval()
        kp_detector.eval()

        return generator, kp_detector

    def make_animation(self, source_image, driving_video, generator, kp_detector, relative=True,
                       adapt_movement_scale=True,
                       cpu=False):
        with torch.no_grad():
            predictions = []
            source = torch.tensor(source_image[np.newaxis].astype(np.float32)).permute(0, 3, 1, 2)
            if not cpu:
                source = source.cuda()
            driving = torch.tensor(np.array(driving_video)[np.newaxis].astype(np.float32)).permute(0, 4, 1, 2, 3)
            kp_source = kp_detector(source)
            kp_driving_initial = kp_detector(driving[:, :, 0])

            for frame_idx in range(driving.shape[2]):
                driving_frame = driving[:, :, frame_idx]
                if not cpu:
                    driving_frame = driving_frame.cuda()
                kp_driving = kp_detector(driving_frame)
                kp_norm = normalize_kp(kp_source=kp_source, kp_driving=kp_driving,
                                       kp_driving_initial=kp_driving_initial, use_relative_movement=relative,
                                       use_relative_jacobian=relative, adapt_movement_scale=adapt_movement_scale)
                out = generator(source, kp_source=kp_source, kp_driving=kp_norm)

                predictions.append(np.transpose(out['prediction'].data.cpu().numpy(), [0, 2, 3, 1])[0])
        return predictions

    def find_best_frame(self, source, driving):
        def normalize_kp(kp):
            kp = kp - kp.mean(axis=0, keepdims=True)
            area = ConvexHull(kp[:, :2]).volume
            area = np.sqrt(area)
            kp[:, :2] = kp[:, :2] / area
            return kp

        fa = face_alignment.FaceAlignment(face_alignment.LandmarksType._2D, flip_input=True, device='cuda')
        kp_source = fa.get_landmarks(255 * source)[0]
        kp_source = normalize_kp(kp_source)
        norm = float('inf')
        frame_num = 0
        for i, image in tqdm(enumerate(driving)):
            kp_driving = fa.get_landmarks(255 * image)[0]
            kp_driving = normalize_kp(kp_driving)
            new_norm = (np.abs(kp_source - kp_driving) ** 2).sum()
            if new_norm < norm:
                norm = new_norm
                frame_num = i
        return frame_num

    def main(self, image, video, result):
        source_image = imageio.imread(image)
        reader = imageio.get_reader(video)
        fps = reader.get_meta_data()['fps']
        driving_video = []
        try:
            for im in reader:
                driving_video.append(im)
        except RuntimeError:
            pass
        reader.close()
        source_image = resize(source_image, (256, 256))[..., :3]
        driving_video = [resize(frame, (256, 256))[..., :3] for frame in driving_video]

        # i = self.find_best_frame(source_image, driving_video)
        i = len(driving_video) // 2
        driving_forward = driving_video[i:]
        driving_backward = driving_video[:(i + 1)][::-1]
        predictions_forward = self.make_animation(source_image, driving_forward, self.generator, self.kp_detector,
                                             relative=True, adapt_movement_scale=True, cpu=False)
        predictions_backward = self.make_animation(source_image, driving_backward, self.generator, self.kp_detector,
                                              relative=True, adapt_movement_scale=True, cpu=False)
        predictions = predictions_backward[::-1] + predictions_forward[1:]

        # predictions = self.make_animation(source_image, driving_video, self.generator, self.kp_detector, relative=True,
        #                                   adapt_movement_scale=True, cpu=False)
        imageio.mimsave(result, [img_as_ubyte(frame) for frame in predictions], fps=fps)



