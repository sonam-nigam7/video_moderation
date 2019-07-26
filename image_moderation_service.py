from bson import ObjectId
from datetime import datetime, timedelta


class ImageModerationService:

    def __init__(self):
        pass

    def ugc_image_mod_task_by_id(self, img_id=None, pid="", type=None):
        print(f"logkey:ImageModTasks,msg: calling function ugc_image_mod_task_by_id.,image_id:{img_id}")
        try:
            self.auto_moderate_ugc_image(img_id, pid, type);
        except Exception as e:
            print(f"logkey:ImageModTasksErr,errMsg: getting an exception while calling auto_moderate_ugc_image, Exception: {e},img_id:{img_id},traceback : {traceback.format_exc()}")
            raise e

    def auto_moderate_ugc_image(self, image_id, pid='', type=None):

        print(f"message: Inside automoderate ugc image. image_id:{image_id} ,pid:{pid},type:{type} logkey: auto_moderate_ugc_image")

        image = self.image_coll.find_one({"_id": ObjectId(str(image_id))}, {"url": 1, "_id": 1, "status": 1})

        if image is None or image.get('url') is None:
            return print(f"message: getting None image for ,image_id :{image_id} , logkey: auto_moderate_ugc_image")

        if image.get('status') in ['approved', 'rejected']:
            return print(f"message: Image is already moderated. image_id:{image_id} ,status:{image.get('status')}, logkey: auto_moderate_ugc_image")

        record = {"id": str(image_id), "url": image.get('url'), "client": "ugc_hotel_images", "pid": pid, "type": type}
        print(f"message: New Image sent for processing. image_id:{image_id} , logkey: auto_moderate_ugc_image")
        self.start_image_moderation(record)

    def start_image_moderation(self, record):

        if record.get('url') is not None and record.get('id') is not None and record.get('client') is not None:
            if record.get('client') in ['voyager']:
                record['id'] = record.get('id')+'_'+record.get('client')

            db_obj = {'_id': record.get('id'), 'client': record.get('client')}
            saved_record = self.image_mod_coll.find_one(db_obj)
            obj = dict(record)
            obj.update(status='created')
            if saved_record is None:
                db_obj.update({'image_url': record.get('url'),'createdAt': datetime.now(),'pid': record.get('pid', ''),'partner':record.get('partner'),'source':record.get('source'),'sourceId':record.get('sourceId')})

                self.image_mod_coll.insert(db_obj)
                print(f"msg: Image moderation record not present in database., record: {record},logkey:start_image_moderation")

                return self.moderate_image(record)


            elif saved_record.get('status') is not None:
                print(f"msg: Image already processed before, record: {record},logkey:start_image_moderation")

                if record.get('client') in ['ingo','voyager']:
                    saved_record.update(id=saved_record.get('_id'),url=saved_record.get('image_url'),partner=record.get('partner'),pid=record.get('pid'))
                    # self.push_data_to_kinesis(saved_record)
                return

            elif saved_record.get('status') is None:
                print(f"message: Image record present but moderation not done., record: {record},logkey: start_image_moderation")
                return self.moderate_image(record)

        else:
            print(f"errmsg: Url or id or client  not present in the requested record., record:{record},logkey:start_image_moderation")

    def moderate_image(self, record, trigger_task=False):

        if record.get('url') is None or record.get('id') is None or record.get('client') is None:

            return print(f"msg: url or id is not present in the requested record., record: {record},logkey: moderate_image")

        image_mod_filters = image_config.get("IMAGE_MOD_FILTERS")
        image_partner_map = image_config.get("KINESIS_PARTNER_MAP")
        partner = image_partner_map.get(record.get('partner', 'default'), 'default')
        filter_list = image_mod_filters.get(record.get('client', ''), {}).get(partner, {}).get('filter_one', [])
        process_next = image_mod_filters.get(record.get('client', ''), {}).get(partner, {}).get('process_next')
        if filter_list is not None and len(filter_list) > 0:
            data = self.moderate_image_with_filters(record, filter_list, process_next)

            if data is not None and data != {} and process_next:
                #### Save record in redis queue
                record.update(tags=data.get('tags'))
                if trigger_task is False:
                    json_data = json.dumps(record)
                    self.redis_con.rpush(self.redis_queue, json_data)
                else:
                    logging.info(
                        f"logkey : moderate_image, msg : Initiating second filters for image, record : {record}")
                    filter_list = image_mod_filters.get(record.get('client', ''), {}).get(partner, {}).get('filter_two',
                                                                                                           [])
                    self.moderate_image_with_filters(record, filter_list, False)


    def moderate_image_with_filters(self,record,filter_list,process_next=True):
        from apps.image_moderation.image_mod_task import update_mod_response_for_ugc_images_task

        db_obj, label_response, tags, tag_relevance_score = {}, [], [], None
        image_mod_status = image_config.get('IMAGE_MOD_STATUS',{})
        kinesis_obj = {'id': record.get('id'), 'tags': record.get('tags', []), 'status': image_mod_status.get('UNTAGGED'),
                       'client': record.get('client'), 'failureCode': '', 'pid': record.get('pid', ''),'partner':record.get('partner'),'url':record.get('url')}

        options = {}
        if record.get('client') in ['voyager']:
            options['output'] = True
        for filter in filter_list:
            response = getattr(ModerationService, filter)(record,options)
            if response.get('success') is False:
                logging.info(f"msg:Moderation Filter is getting failed!,filter:{filter},logkey:self.logkey")
                db_obj.update(response.get('db_obj',{}))
                kinesis_obj.update(response.get('kinesis_obj'))
                self.image_mod_coll.update({'_id': record['id'], 'client': record['client']},{"$set":db_obj})
                if (record.get('client') in self.ugc_client):
                    update_mod_response_for_ugc_images_task.apply_async([kinesis_obj], countdown=1)
                elif(record.get('client') in ['ingo','voyager']):
                    self.push_data_to_kinesis(kinesis_obj)
                return
            tags = response.get('db_obj', {}).get('tags', []) if filter == 'classification_filter' else tags
            label_response = response.get('db_obj', {}).get('visionResp', []) if filter == 'safe_search_filter' else label_response

            db_obj.update(response.get('db_obj',{}))
            kinesis_obj.update(response.get('kinesis_obj',{}))

        if tags and label_response:
            image_tag_relevance_score = self.get_image_tag_relevance_score(tags, label_response)
            if bool(image_tag_relevance_score):
                tag_relevance_score = image_tag_relevance_score.get('tagRelevanceScore')
                db_obj.update({'qualityScore': image_tag_relevance_score})
                if record.get('client') in self.ugc_client:
                    self.image_coll.update({'_id': ObjectId(str(record['id']))}, {"$set": {'qualityScore': image_tag_relevance_score}})

        if record.get('client') in self.ugc_client and tag_relevance_score and tag_relevance_score <= category_config.get('MIN_TAG_RELEVANCE_SCORE', -1):
            _status = image_mod_status.get('REJECTED')
            db_obj.update({"failureCode": "LOW_TAG_RELEVANCE_SCORE", "processedAt": datetime.now(), "status": _status})
            self.image_mod_coll.update({'_id': record['id'], 'client': record['client']}, {"$set": db_obj})
            kinesis_obj.update({'failureCode':"LOW_TAG_RELEVANCE_SCORE", 'status':_status})
            update_mod_response_for_ugc_images_task.apply_async([kinesis_obj], countdown=1)
            return

        if process_next == False:
            kinesis_obj.update(status=image_mod_status.get('ACCEPTED'))
            db_obj.update(status=image_mod_status.get('ACCEPTED'))
            if (record.get('client') in self.ugc_client):
                update_mod_response_for_ugc_images_task.apply_async([kinesis_obj], countdown=1)
            elif(record.get('client') in ['ingo','voyager']):
                self.push_data_to_kinesis(kinesis_obj)

        db_obj.update(processedAt= datetime.now())
        self.image_mod_coll.update({'_id': record['id'], 'client': record['client']},
                                    {"$set": db_obj})
        logging.info({"log_key": "image_moderation","method":"moderate_image_with_filters", 'id': record.get('id'), 'update': db_obj,
                      'input': {'_id': record['id'], 'client': record['client']}})

        return {"tags":db_obj.get("tags")}
