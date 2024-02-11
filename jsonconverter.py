import json
from pathlib import Path
import os
import capnp
from PIL import Image
from io import BytesIO

messages = capnp.load("deepdrr_zmq/deepdrrzmq/messages.capnp")
def extract_topic_data_from_log(log_file,log_folder_path):
    entries = messages.LogEntry.read_multiple_bytes(log_file.read_bytes())
    topic_data = []
    unique_topics = []
    i = 0
    image_idx = 0
    for entry in entries:
        topic = entry.topic.decode('utf-8')
        msgdict = {'topic': topic}
        file_name = os.path.splitext(log_file.name)[0] 
        file_number = file_name.split("--")[-1] 
        # print(file_number + ' file '+str(len(topic_data))+' '+topic)#for debug
        if topic not in unique_topics:  # Add unique topics to the list
            unique_topics.append(topic)

        if topic.startswith("/mp/transform/"):
            with messages.SyncedTransformUpdate.from_bytes(entry.data) as transform:
                # transform_dict = {}
                msgdict['timestamp'] = transform.timestamp
                msgdict['clientId'] = transform.clientId
                transforms = []
                for i in range(len(transform.transforms)):
                    transforms.append([x for x in transform.transforms[i].data])
                msgdict['transforms'] = transforms
                # msgdict['transforms'] = transform_dict 
        if topic.startswith("/mp/time/"):
            with messages.Time.from_bytes(entry.data) as time:
                msgdict['time'] = time.millis 

        if topic.startswith("project_request/"):
            with messages.ProjectRequest.from_bytes(entry.data) as request:
                msgdict['requestId'] = request.requestId
                msgdict['projectorId'] = request.projectorId
                cameraProjections_dict_ = []
                for i in range(len(request.cameraProjections)):
                    current_cameraProjections = request.cameraProjections[i]
                    cameraProjections_dict = {}
                    camerainstrinsic_dict = {}
                    camerainstrinsic_dict['sensorHeight'] = current_cameraProjections.intrinsic.sensorHeight
                    camerainstrinsic_dict['sensorWidth'] = current_cameraProjections.intrinsic.sensorWidth
                    camerainstrinsic_dict['pixelSize'] = current_cameraProjections.intrinsic.pixelSize
                    camerainstrinsic_dict['sourceToDetectorDistance'] = current_cameraProjections.intrinsic.sourceToDetectorDistance
                    cameraProjections_dict['intrinsic'] = camerainstrinsic_dict
                    cameraProjections_dict['extrinsic'] = list(request.cameraProjections[i].extrinsic.data)   
                    cameraProjections_dict_.append(cameraProjections_dict)
                msgdict['cameraProjections'] = cameraProjections_dict_ 
                transforms = []
                for i in range(len(request.volumesWorldFromAnatomical)):
                    transforms.append([x for x in request.volumesWorldFromAnatomical[i].data])
                msgdict['volumesWorldFromAnatomical'] = transforms 
        if topic.startswith("/project_response/"):
        #     decode  the jpeg image from the bytes
            image = Image.open(BytesIO(entry.data))
            image_filename = str(image_idx) + ".jpg"
            image_path = os.path.join(log_folder_path, image_filename)
            image.save(image_path)
            image_idx += 1

        if topic.startswith("/mp/setting"):
            with messages.SycnedSetting.from_bytes(entry.data) as setting_data:
                setting_data_dict = {}
                msgdict['timestamp'] = setting_data.timestamp
                msgdict['clientId'] = setting_data.clientId
                which = setting_data.setting.which()
                if which == 'uiControl':
                    setting = setting_data.setting.uiControl                   
                    setting_data_dict['patientMaterial'] = setting.patientMaterial
                    setting_data_dict['annotationSelection'] = list(setting.annotationError)
                    setting_data_dict['corridorIndicator'] = setting.corridorIndicator
                    setting_data_dict['carmIndicator'] = setting.carmIndicator
                    setting_data_dict['webcorridorerrorselect'] = setting.webcorridorerrorselect
                    setting_data_dict['webcorridorselection'] = setting.webcorridorselection
                    setting_data_dict['flippatient'] = setting.flippatient
                    setting_data_dict['viewIndicatorselfselect'] = setting.viewIndicatorselfselect
                    msgdict['uiControl'] = setting_data_dict   
                if which == 'arm':     
                    setting = setting_data.setting.arm.liveCapture  
                    msgdict['liveCapture'] = setting          
        topic_data.append(msgdict)
    return topic_data, unique_topics
def convert_pvrlog_to_json(log_folder):
    log_folder_path = Path(log_folder)
    pvrlog_files = log_folder_path.glob("*.pvrlog")
    for log_file in pvrlog_files:
        json_file_path = log_folder_path /f"{log_file.stem}.json"
        img_folder_path = log_folder_path / f"image"
        os.makedirs(img_folder_path, exist_ok=True)
        topic_data ,unique_topics= extract_topic_data_from_log(log_file,img_folder_path)
        with open(json_file_path, 'w') as json_file:
            json.dump(topic_data, json_file, indent=4)
        # print(f"Converted {log_file.name} to JSON.")#for debug
    # print('--------------Unique Topics--------------')
    # for topic in unique_topics:
    #     print(topic)
    print('---------------Convert Complete--------------')

if __name__ == '__main__':
    # log_folder = input("Enter the folder path containing .pvrlog files: ")
    log_folder = "C:/vrplog/zggdi8m5m8aql2bn--2023-06-24-23-39-57"
    convert_pvrlog_to_json(log_folder)