from Api import InstagramAPI
import json
import threading
import logging
import os
from pathlib import Path
from autocrop import Cropper
from random import choice
import requests
import time
import pickle
from deepfake import Fake
import json
import multiprocessing
import subprocess
import numpy as np
from numpy import mean
import cv2
import copy
from PIL import Image
from autocrop import Cropper
import shutil
import datetime
import re
import torch.multiprocessing as mp
import traceback
import sys

logging.basicConfig(format="%(asctime)s - %(levelname)s: %(message)s", level=logging.INFO, datefmt="%I:%M:%S")
TEMP_PATH = "temp"
FILES_PATH = "files"
WIDTH, HEIGHT = 256, 256
cropper = Cropper(width=256, height=256, smoother=True)


class Checker:
    def __init__(self, session):
        logging.info("Initialising Checker-Agent.")
        self.session = session
        self.replies_start = ["Hello! I make DeepFake videos \U0001F916.\nUse me with /start"]
        self.replies_photo = ["Aight! Send me a photo \U0001F5BC.\nMake sure that the face is clearly visible",
                              "Let's do this. Send me a photo with the face clearly visible \U0001F5BC",
                              "Here we go. Send me a photo and make sure the face is clearly visible \U0001F5BC"]
        self.replies_video = ["Photo is ready \U0001F5BC! Now send the video \U0001F39E.\nAgain make sure the face is clearly visible "
                              "for good results!"]  # use 100
        self.deny_media = ["In order to use me, type /start first and wait for my response \U0001F916."]
        self.deny_video = [
            "That's not correct \U0000274C. Please send the photo first \U0001F5BC!"]  # if someone sends video before photo
        self.deny_start = [
            "You already started making one DeepFake \U0000203C. Please wait until I'm done editing this \U0001F916"]
        self.wait = ["Well done, I have everything I need \U0001F916. I'll edit your deepfake now and send it as soon "
                     "as it's ready \U0001F3A8!"]
        self.queue = [
            f"There are currently {self.get_queue_size()} people in the queue \U0001F465.\nEstimated waiting times for "
            f"non-donators are currently at \U000023F0:\n{self.get_average_waiting_time()}.\n\nWant to get your videos faster \U000023E9?\n~Message me with /donate \U0001F607",
            f"{self.get_queue_size()} people are currently in the queue \U0001F465.\nEstimated waiting times for "
            f"non-donators are currently at \U000023F0:\n{self.get_average_waiting_time()}.\n\nWant to get your videos faster \U000023E9?\n~Message me with /donate \U0001F607"]
        self.donate = [
            "\U0001F4B8 Donations \U0001F4B8\n\nEven though all the models we use are open source, they require powerful computing "
            "resources.\nThis is why we need your financial support, which will be used to pay for "
            "servers (monthly server-costs are currently at $150)\n\nDonations will also result in benefits "
            "for you \U0001F607:\n \U00002666 Video duration limit: More than 10 seconds\n \U00002666 Priority queue (get your videos before "
            "everyone else!)\n \U00002666 Watermark removal\n \U00002666 You can find more information on our Patreon - Page!\n\nTo make it fair, the benefits will be given to donations from 3€/$ upwards. If you "
            "donated, message @dome271.\n\nThanks for helping making this service more accessible for "
            "everyone!\n\nDonation Options:\n\nPatreon: patreon.com/deepfake_py\nPaypal: paypal.me/dome271"]
        self.help = ["Oh you need help ? \U0001F60E Here are all the commands "
                     "available:\n\n\U0001F534 /start\n\n\U0001F7E2 /donate\n\n\U0001F7E1 /queue\n\n\U0001F535 /stats\n\n\U0001F7E0 /information\n\n\U0001F7E3 /about\n\nIf you have more in depth questions, message me on "
                     "@dome271 \U0001F920"]
        self.about = ["\U000025FC\U0001F535 About \U0001F535\U000025FC\nThis DeepFake - Maker uses the paper "
                            "'First Order Motion Model for Image Animation' by Aliaksandr Siarohin et al. under the "
                            "hood for the Image Animation"]
        self.information = ["Here are some general information about the bot \U0001F916. It took me about 2 1/2 weeks making "
                            "this bot with about 96 hours of coding, fixing errors and setting up the server etc. At "
                            "some points I encountered errors I've never seen before which required hours of googling "
                            "how to fix it \U0001F629. Nontheless I'm proud now to have it finished and hope it will get at "
                            "least some financial support to maintain the servers (which I can't do since I'm still a "
                            "student \U0001F468). It is now my biggest project I've ever made on my own and hope I can add even "
                            "more fantastic features in the future if people like the bot \U0001F91D! Until then I hope you have "
                            "a nice time and stay healthy \U0001F64F! If you have any questions about the bot, feel free to DM "
                            "me on my personal account @dome271 \U0001F4AA"]

    def get_queue_size(self):
        n = 0
        for item in os.listdir(TEMP_PATH):
            if len(os.listdir(os.path.join(TEMP_PATH, item))) == 3:
                n += 1
        return n

    def get_queue_place(self, user_id):
        queue = sorted([item for item in os.listdir(TEMP_PATH) if len(os.listdir(os.path.join(TEMP_PATH, item))) == 3], key=lambda x: os.path.getctime(os.path.join(TEMP_PATH, x)))
        try:
            index = queue.index(user_id) + 1
        except ValueError:
            index = False
        return index

    def get_average_waiting_time(self):
        with open("log.json") as log_file:
            content = json.load(log_file)
            response_times = content["response_time"]
            if len(response_times) <= 10:
                avg_response_time = int(mean(response_times))
            else:
                avg_response_time = int(mean(response_times[-10:]))
            avg_response_time = str(datetime.timedelta(seconds=avg_response_time)).split(":")
            if avg_response_time[0] == "0":
                return f"{avg_response_time[1]} minutes and {avg_response_time[2]} seconds"
            else:
                return f"{avg_response_time[0]} hours, {avg_response_time[1]} minutes and {avg_response_time[2]} seconds"

    def get_stats(self):
        with open("log.json") as log_file:
            content = json.load(log_file)
            num_deepfakes = content["num_deepfakes"]
            num_users = len(content["users"])
            return num_deepfakes, num_users

    def create_user_json(self, username, dir_path):
        open(os.path.join(dir_path, "user.json"), "w")
        with open(os.path.join(dir_path, "user.json"), "r+") as user_file:
            json.dump(json.loads('{"username": "", "start_time": ""}'), user_file)
            user_file.seek(0)
            content = json.load(user_file)
            content["username"] = username
            content["start_time"] = time.time()
            user_file.seek(0)
            json.dump(content, user_file)
            user_file.truncate()

    def main(self):
        lastResponse = None
        while True:
            self.session.getv2Inbox()
            response = json.loads(json.dumps(self.session.LastJson))
            if response is False or response == {'message': 'Please wait a few minutes before you try again.', 'status': 'fail'}:
                logging.info("Checker: Inbox repetition error -> Sleeping 120 seconds now.")
                time.sleep(120)
                continue

            if response == lastResponse:
                logging.info("Checker: Inbox repetition error -> Sleeping 60 seconds now.")
                time.sleep(60)
                continue

            if response["pending_requests_total"] != 0:
                self.session.get_pending_inbox()
                inbox = self.session.LastJson

                for i in inbox["inbox"]["threads"]:
                    self.session.approve_pending_thread(i["thread_id"])

            for i in response["inbox"]["threads"]:
                username = i["users"][0]["username"]
                # if username not in ["dome271", "haydenm2727"]:
                #     continue
                user_id = str(i["users"][0]["pk"])
                try:
                    if i["items"][0]["item_type"] == "text":
                        text = i["items"][0]["text"]
                        if text == "/start":
                            with open("log.json", "r+") as log_file:
                                content = json.load(log_file)
                                if user_id not in content["users"]:
                                    content["users"].append(user_id)
                                    log_file.seek(0)
                                    json.dump(content, log_file)
                                    log_file.truncate()

                            if not os.path.exists(os.path.join(TEMP_PATH, user_id)):
                                logging.info(f"Checker: Starting session for {username}.")
                                self.session.sendMessage(user_id, choice(self.replies_photo))
                                os.mkdir(os.path.join(TEMP_PATH, user_id))
                            else:
                                self.session.sendMessage(user_id, choice(self.deny_start))

                        elif text == "/donate":
                            self.session.sendMessage(user_id, choice(self.donate))

                        elif text == "/queue":
                            queue_place = self.get_queue_place(user_id)
                            if queue_place:
                                queue = [
                                    f"There are currently {self.get_queue_size()} people in the queue \U0001F465. Youre current place in the queue is: {queue_place}.\nYour estimated "
                                    f"waiting time is {self.get_average_waiting_time()}\n\nWant to get your videos faster "
                                    f"\U000023E9?\n~Message me with /donate \U0001F607"]
                                self.session.sendMessage(user_id, choice(queue))
                            else:
                                queue = [
                                    f"There are currently {self.get_queue_size()} people in the queue \U0001F465.\nThe estimated "
                                    f"waiting time is {self.get_average_waiting_time()}\n\nWant to get your videos faster "
                                    f"\U000023E9?\n~Message me with /donate \U0001F607"]
                                self.session.sendMessage(user_id, choice(queue))

                        elif text == "/help":
                            self.session.sendMessage(user_id, choice(self.help))

                        elif text == "/about":
                            self.session.sendMessage(user_id, choice(self.about))

                        elif text == "/stats":
                            num_deepfakes, num_users = self.get_stats()
                            stats = [
                                f"\U000025FC\U0001F535 Stats \U0001F535\U000025FC\nI have already created {num_deepfakes} DeepFakes and there were already {num_users} nice people using me! \U0001F916"]
                            self.session.sendMessage(user_id, choice(stats))

                        elif text == "/information":
                            self.session.sendMessage(user_id, choice(self.information))

                        else:
                            if str(i["items"][0]["user_id"]) == user_id:
                                self.session.sendMessage(user_id, choice(self.replies_start))

                    elif i["items"][0]["media"]["media_type"] == 1:  # photo
                        if os.path.exists(os.path.join(TEMP_PATH, user_id)):

                            temp_w, temp_h = 10000, 10000
                            url = None
                            for version in i["items"][0]["media"]["image_versions2"]["candidates"]:
                                w, h = version["width"], version["height"]
                                if 256 <= w < temp_w and 256 <= h < temp_h:
                                    url = version["url"]
                            if url is None:
                                url = i["items"][0]["media"]["image_versions2"]["candidates"][0]["url"]

                            photo = requests.get(url)
                            open(os.path.join(TEMP_PATH, user_id, "photo.jpg"), "wb").write(photo.content)
                            self.session.sendMessage(user_id, choice(self.replies_video))
                        else:
                            self.session.sendMessage(user_id, choice(self.deny_media))

                    elif i["items"][0]["media"]["media_type"] == 2:  # video
                        if os.path.exists(os.path.join(TEMP_PATH, user_id)):
                            if len(os.listdir(os.path.join(TEMP_PATH, user_id))) == 1:

                                self.create_user_json(username, Path(os.path.join(TEMP_PATH, user_id)))

                                temp_w, temp_h = 10000, 10000
                                url = None
                                for version in i["items"][0]["media"]["video_versions"]:
                                    w, h = version["width"], version["height"]
                                    if 256 <= w < temp_w and 256 <= h < temp_h:
                                        url = version["url"]
                                if url is None:
                                    url = i["items"][0]["media"]["video_versions"][0]["url"]

                                video = requests.get(url)
                                open(os.path.join(TEMP_PATH, user_id, "video.mp4"), "wb").write(video.content)
                                self.session.sendMessage(user_id, choice(self.wait))
                                queue = [
                                    f"There are currently {self.get_queue_size()} people in the queue \U0001F465. Your estimated "
                                    f"waiting time is {self.get_average_waiting_time()}\n\nWant to get your videos faster "
                                    f"\U000023E9?\n~Message me with /donate \U0001F607"]
                                self.session.sendMessage(user_id, choice(queue))
                            else:
                                self.session.sendMessage(user_id, choice(self.deny_video))
                        else:
                            self.session.sendMessage(user_id, choice(self.deny_media))
                except:
                    pass
                time.sleep(1)
            # logging.info("Checker: Sleeping 10 seconds now.")
            lastResponse = copy.deepcopy(response)
            time.sleep(60)


class Editor:
    def __init__(self, session, deepfake):
        logging.info("Initialising Editor-Agent.")
        self.session = session
        self.max_duration = 10
        self.deepfake = deepfake
        self.no_faces = ["Unfortunately I could not recognize any faces in the video you sent \U00002639\nWhy don't you try another video? Type /start to begin again! \U0001F61D"]

    def video_too_long(self, level):
        max_durations = {0: 10, 1: 30, 2: 45}
        max_duration = max_durations[level]
        return f"Hey \U0001F916, your video was longer than the maximum length of {max_duration} seconds \U0001F60E. It's no problem, I just took the first {max_duration} seconds and create the DeepFake now! \U0001F913\n\nIf you wish to create longer DeepFakes, consider donating \U0001F680. For more information message me with /donate"

    def has_donated(self, user_id):
        with open("log.json") as log_file:
            content = json.load(log_file)
            if user_id in content["donator"]:
                return True
            else:
                return False

    def has_donated_new(self, user_id):
        with open("other_tools/donator.json") as don_file:
            content = json.load(don_file)
            donator = content["donator"].keys()
            if user_id in donator:
                return content["donator"][user_id]
            else:
                return 0

    def get_video_length(self, video):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", video],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        return float(result.stdout)

    def get_video_fps(self, video):
        result = subprocess.run(f"ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries "
                       f"stream=r_frame_rate {video}",
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
        clean_result = re.sub("[^0-9/]", "", result)
        return eval(clean_result)

    def auto_crop(self, frame):
        height, width = frame.shape[:2]
        width_half = width // 2
        height_half = height // 2
        if width > height:
            x, y = width_half - height_half, 0
            out_w = out_h = height
        elif width < height:
            x, y = 0, height_half - width_half
            out_w = out_h = width
        else:
            x, y = 0, 0
            out_w = out_h = width
        return frame[y:y + out_h, x:x + out_w]

    def resize_image(self, image):
        img = cv2.imread(image)
        cropped_array = cropper.crop(img)

        if cropped_array is None:
            cropped_array = self.auto_crop(img)
            cv2.imwrite(image, cropped_array)
        else:
            cropped_array = img[int(cropped_array[0]):int(cropped_array[1]), int(cropped_array[2]):int(cropped_array[3])]
            cropped_array = cv2.resize(cropped_array, (256, 256), interpolation=cv2.INTER_AREA)
            cv2.imwrite(image, cropped_array)

    def resize_video(self, video, crop):
        def get_better_frame(images, i, start_i, cropper, check=False):
            if i - start_i > 100:
                return False
            try:
                position = cropper.crop(images[i + 1])
                if position is None:
                    return get_better_frame(images, i + 1, start_i, cropper)
                else:
                    if not check:
                        positions[i + 1] = position
                        return True
                    else:
                        return True
            except IndexError:
                return False

        read_video = cv2.VideoCapture(video)
        fps = read_video.get(cv2.CAP_PROP_FPS)
        num_frames = read_video.get(cv2.CAP_PROP_FRAME_COUNT) - 1
        height, width = read_video.get(cv2.CAP_PROP_FRAME_HEIGHT), read_video.get(cv2.CAP_PROP_FRAME_WIDTH)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        write_video = cv2.VideoWriter(crop, fourcc, fps, (256, 256))
        images = []
        positions = {}

        success, image = read_video.read()
        count = 0
        while success:
            images.append(image)
            success, image = read_video.read()
            count += 1

        for i in range(len(images)):
            if i % 10 == 0 or i == num_frames:
                position = cropper.crop(images[i])
                if i == 0 and position is None:
                    check = get_better_frame(images, i, i, cropper, check=True)
                    if not check:
                        return None

                if i == 0 and position is None:
                    width_half = width // 2
                    height_half = height // 2
                    if width > height:
                        x, y = width_half - height_half, 0
                        out_w = out_h = height
                    elif width < height:
                        x, y = 0, height_half - width_half
                        out_w = out_h = width
                    else:
                        x, y = 0, 0
                        out_w = out_h = width
                    positions[0] = [y, y + out_h, x, x + out_w]  # [y, x, y+height_half, x+width_half]

                if position is None:
                    check = get_better_frame(images, i, i, cropper, check=False)
                    if not check:
                        # happens if Indexerror arised in get_better_frame -> current frame <---> last frame : no faces --> break out
                        break
                else:
                    positions[i] = position

        if len(positions) < num_frames * 0.05:
            return None

        keys = list(positions.keys())
        values = list(positions.values())
        for i in range(len(keys)):
            key1, value1 = keys[i], values[i]
            try:
                key2, value2 = keys[i + 1], values[i + 1]
            except IndexError:  # only happens if key1 and value1 are the last entries --> simply break out
                continue
            new_keys = list(range(key1 + 1, key2))
            new_values = np.round(np.linspace(value1, value2, len(new_keys) + 1, endpoint=False)).tolist()[1:]
            for key, value in zip(new_keys, new_values):
                positions[key] = value

        for item in sorted(positions.items(), key=lambda k: k[0]):
            frame_num, position = item
            cropped_image = images[frame_num][int(position[0]): int(position[1]), int(position[2]): int(position[3])]
            image = cv2.resize(cropped_image, (256, 256), interpolation=cv2.INTER_AREA)
            write_video.write(image)

        return sorted(list(positions.keys()))[0]

    def combine_audio_video(self, org_video, deepfake_video, user_id, first_frame):
        """
        Take audio from original audio and combine it with result video
        Apply watermark to video
        """
        org_video = os.path.abspath(org_video)
        deepfake_video = os.path.abspath(deepfake_video)
        temp_video = os.path.abspath(Path(os.path.join(TEMP_PATH, user_id, "temp_result.mp4")))
        temp_audio = os.path.abspath(Path(os.path.join(TEMP_PATH, user_id, "temp_audio.aac")))
        watermark_video = os.path.abspath(os.path.join(FILES_PATH, "watermark.gif"))
        result_video = os.path.abspath(os.path.join(TEMP_PATH, user_id, "finished.mp4"))
        if first_frame == 0:
            level = self.has_donated_new(user_id)
            if level in [0, 1]:
                subprocess.call(
                    f'ffmpeg -loglevel panic -i {deepfake_video} -i {org_video} -c copy -map 0:v:0 -map 1:a:0 -shortest {temp_video}',
                    shell=True)
                subprocess.call(f'ffmpeg -loglevel panic -i {temp_video} -i {watermark_video} -filter_complex overlay=0:0 {result_video}',
                                shell=True)
            else:
                subprocess.call(
                    f'ffmpeg -loglevel panic -i {deepfake_video} -i {org_video} -c copy -map 0:v:0 -map 1:a:0 -shortest {result_video}',
                    shell=True)
                open(os.path.join(TEMP_PATH, user_id, "placeholder.txt"), "w")

        else:
            fps = self.get_video_fps(org_video)
            start_audio = first_frame / fps
            subprocess.call(f"ffmpeg -i video.mp4 -ss {start_audio} -vn -acodec copy {temp_audio}", shell=True)
            subprocess.call(f"ffmpeg -i {deepfake_video} -i {temp_audio} -c:v copy -c:a aac -shortest {temp_video}")
            os.remove(deepfake_video)  # remove such that number of files in directory is the same
            subprocess.call(f'ffmpeg -i {temp_video} -i {watermark_video} -filter_complex overlay=0:0 {result_video}',
                            shell=True)

    def main(self):
        while True:
            try:
                queue = sorted(os.listdir(TEMP_PATH), key=lambda x: os.path.getctime(os.path.join(TEMP_PATH, x)))

                for user in queue[::-1]:
                    if self.has_donated_new(user):
                        queue.insert(0, queue.pop(queue.index(user)))

                for item in queue:
                    if len(os.listdir(os.path.join(TEMP_PATH, item))) == 3:  # Check if result has not been created yet
                        with open(os.path.join(TEMP_PATH, item, "user.json")) as user_file:
                            content = json.load(user_file)
                            username = content["username"]
                        logging.info(f"Editor: Starting to edit DeepFake for {username}.")
                        photo = Path(os.path.join(TEMP_PATH, item, "photo.jpg"))
                        video = Path(os.path.join(TEMP_PATH, item, "video.mp4"))
                        crop = Path(os.path.join(TEMP_PATH, item, "crop.mp4"))
                        temp_video = Path(os.path.join(TEMP_PATH, item, "temp.mp4"))
                        result = Path(os.path.join(TEMP_PATH, item, "result.mp4"))

                        #  check if video is longer than t, shorten it. If longer, write message to user
                        video_path = os.path.abspath(video)
                        temp_path = os.path.abspath(temp_video)
                        # if round(self.get_video_length(video_path)) > self.max_duration and not self.has_donated(item):
                        video_length = self.get_video_length(video_path)
                        level = self.has_donated_new(item)

                        if video_length > self.max_duration and level == 0:
                            subprocess.call(f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:10 -c copy {temp_path}",
                                            shell=True)
                            os.remove(video)
                            os.rename(temp_video, video)
                            self.session.sendMessage(item, self.video_too_long(0))

                        elif video_length > 30 and level == 1:  # normal patreon
                            subprocess.call(f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:30 -c copy {temp_path}",
                                            shell=True)
                            os.remove(video)
                            os.rename(temp_video, video)
                            self.session.sendMessage(item, self.video_too_long(1))

                        elif video_length > 45 and level == 2:  # lovely patreon
                            subprocess.call(f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:45 -c copy {temp_path}",
                                            shell=True)
                            os.remove(video)
                            os.rename(temp_video, video)
                            self.session.sendMessage(item, self.video_too_long(2))

                        else:
                            subprocess.call(
                                f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:{video_length} -c copy {temp_path}",
                                shell=True)
                            os.remove(video)
                            os.rename(temp_video, video)

                        # if not self.has_donated(item):
                        #     if video_length > self.max_duration:
                        #         subprocess.call(f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:10 -c copy {temp_path}",
                        #                         shell=True)
                        #         os.remove(video)
                        #         os.rename(temp_video, video)
                        #         self.session.sendMessage(item, choice(self.too_long))
                        #     else:
                        #         subprocess.call(
                        #             f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:{video_length} -c copy {temp_path}",
                        #             shell=True)
                        #         os.remove(video)
                        #         os.rename(temp_video, video)
                        # else:
                        #     subprocess.call(
                        #         f"ffmpeg -loglevel panic -ss 00:00:00 -i {video_path} -to 00:00:{video_length} -c copy {temp_path}",
                        #         shell=True)
                        #     os.remove(video)
                        #     os.rename(temp_video, video)

                        self.resize_image(os.path.relpath(photo))
                        first_frame = self.resize_video(os.path.relpath(video), os.path.relpath(crop))
                        if first_frame is None:
                            # Video doesnt contain faces
                            shutil.rmtree(os.path.join(TEMP_PATH, item), ignore_errors=True)
                            self.session.sendMessage(item, choice(self.no_faces))
                            continue
                        self.deepfake.main(photo, crop, result)
                        self.combine_audio_video(video, result, item, first_frame)
            except Exception:
                print(traceback.format_exc())
                print(sys.exc_info()[2])


class Sender:
    def __init__(self, session):
        logging.info("Initialising Sender-Agent.")
        self.message = [
            "Here is your video \U00002757\n\nIf this account gets banned, updates for new Deepfake-Bots will be "
            "released on \U0001F535@deepfake.py\U0001F535\nMake sure to follow us there!\n\nIf you want to receive your "
            "videos faster or simply want to support us, message me with /donate \U0001F607"]
        self.session = session

    def main(self):
        while True:
            try:
                queue = sorted(os.listdir(TEMP_PATH), key=lambda x: os.path.getctime(os.path.join(TEMP_PATH, x)))
                for item in queue:
                    if len(os.listdir(os.path.join(TEMP_PATH, item))) == 7:
                        # Check if result is already created (5 because => photo, org_video, deepfake_video, temp_video, temp_audio, result_video, crop_video, user.json
                        time.sleep(5)
                        result = Path(os.path.join(TEMP_PATH, item, "finished.mp4"))
                        self.session.sendVideo(item, result)
                        self.session.sendMessage(item, choice(self.message))

                        with open(os.path.join(TEMP_PATH, item, "user.json")) as user_file:
                            content = json.load(user_file)
                            username = content["username"]
                            start_time = content["start_time"]
                            difference = round(time.time() - start_time)

                        logging.info(f"Sender: Successfully sent DeepFake to {username}.")

                        with open("log.json", "r+") as log_file:
                            content = json.load(log_file)
                            content["response_time"].append(difference)
                            content["num_deepfakes"] += 1
                            log_file.seek(0)
                            json.dump(content, log_file)
                            log_file.truncate()

                        shutil.rmtree(os.path.join(TEMP_PATH, item), ignore_errors=True)
                    # logging.info("Sender: Sleeping 10 seconds now.")
            except Exception:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            time.sleep(10)


def main(d):
    username = ""
    password = ""
    session = InstagramAPI(username, password)
    if os.path.exists("session"):
        logging.info("Loading Instagram session....")
        session = pickle.load(open("session", "rb"))
    else:
        logging.info("Logging into Instagram Account and saving session....")
        session.login()
        pickle.dump(session, open("session", "wb"))
    c = Checker(session)
    e = Editor(session, d)
    s = Sender(session)
    c_process = multiprocessing.Process(target=c.main)
    c_process.start()
    e_process = multiprocessing.Process(target=e.main)
    e_process.start()
    s_process = multiprocessing.Process(target=s.main)
    s_process.start()


if __name__ == '__main__':
    mp.set_start_method("spawn", force=True)
    DEEPFAKE = Fake()
    main(DEEPFAKE)
