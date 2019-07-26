import urllib.request
import cv2
import os


class ImagExtractorFromVideo:
    def __init__(self):
        pass

    def download_video(self, video_url, video_path):
        try:

            # creating a folder named data
            if not os.path.exists('data'):
                os.makedirs('data')

            # if not created then raise error
        except OSError:
            print('Error: Creating directory of data')
        video_url = 'https://gi-ugcvideos.s3.ap-south-1.amazonaws.com/Rohtak-Hotel-iotaa---Do-Not-Book-QC-1552409933564.mp4'
        video_path = '/data/testvideo.mp4'
        try:
            print('running')
            urllib.request.urlretrieve(video_url, video_path)
            print('video downloaded')
            return video_path
        except Exception as e:
            print('getting error while downloading video')
            print(e)
            return None

    def extract_images_from_video(self, video_path):
        video_path = '/Users/piyush.tyagi/Downloads/Rohtak-Hotel-iotaa---Do-Not-Book-QC-1552409933564.mp4'
        cam = cv2.VideoCapture(video_path)

        try:

            # creating a folder named data
            if not os.path.exists('data'):
                os.makedirs('data')

            # if not created then raise error
        except OSError:
            print('Error: Creating directory of data')

        # frame
        currentframe = 0

        while True:

            # reading from frame
            ret, frame = cam.read()
            cam.set(cv2.CAP_PROP_POS_MSEC, (currentframe * 1000))

            if ret:
                # if video is still left continue creating images
                name = './data/frame' + str(currentframe) + '.jpg'
                print('Creating...' + name)

                # writing the extracted images
                cv2.imwrite(name, frame)

                # increasing counter so that it will
                # show how many frames are created
                currentframe += 1
            else:
                break

        # Release all space and windows once done
        cam.release()
        cv2.destroyAllWindows()
