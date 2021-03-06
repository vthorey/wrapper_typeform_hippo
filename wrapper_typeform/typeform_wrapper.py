import requests
import pandas as pd
import time
import json

class Client(object):
    
    
    _VALID_VERSIONS = ['v1']

    
    type_question=['legal',
                 'date',
                 'yes_no',
                 'rating',
                 'number',
                 'opinion_scale',
                 'website',
                 'long_text',
                 'email',
                 'short_text',
                'dropdown',
                'multiple_choice']
    
    
    def __init__(self, access_token=None, version=None):
        self.access_token = access_token
        if version not in self._VALID_VERSIONS:
            self.version = self._VALID_VERSIONS[0]
        if access_token:
            self.auth = ClientAuth(access_token=access_token)
        else:
            print("You must provide an access_token")
            
            
            
    def typeform_to_DF (self,typeform_id):
        
        
        

        form=requests.get('https://api.typeform.com/forms/'+typeform_id, headers={'authorization': 'bearer '+self.auth()})
        
        
        if form.status_code!=200:
            form=form.json()
            print('Error: '+str(form['code']))
            print(form['description'])
            return(None,None)
        
        else:
            
            form=form.json()

            print("Getting questions from the API")

            questions=[t for t in form['fields'] if 'validations' in t.keys()]+[item for sublist in [u['fields'] for u in [t['properties'] for t in form['fields'] if t['type']=='group'] ] for item in sublist] 

            print("Getting responses from the API")

            reponses=[]
            responses_temp=requests.get('https://api.typeform.com/forms/'+typeform_id+'/responses'+'?page_size=500&sort=submited_at&completed=1', headers={'authorization': 'bearer '+self.auth()})
            responses_temp=responses_temp.json()


            while len(responses_temp['items'])==500:
                reponses+=responses_temp['items']
                last_token=responses_temp['items'][499]['token']

                responses_temp=requests.get('https://api.typeform.com/forms/'+typeform_id+'/responses'+'?page_size=500&sort=submited_at&completed=1&after='+last_token, headers={'authorization': 'bearer '+self.auth()})
                responses_temp=responses_temp.json()


            reponses+=responses_temp['items']


            print("Data processing")


            print("We create the questions list")
            question_DS=[]
            for i in range(len(questions)):
                id=str(questions[i]['id'])
                title=questions[i]['title']
                type=questions[i]['type']

                if type in ['legal','yes_no']:
                    possible_answer='[0,1]'
                    question_DS.append([id,id,title,possible_answer,type])


                elif type=='date':
                    possible_answer='MMDDYYYY'
                    question_DS.append([id,id,title,possible_answer,type])


                elif type=='rating':
                    possible_answer='[1,'+str(questions[i]['properties']['steps'])+']'
                    question_DS.append([id,id,title,possible_answer,type])


                elif type=='number':
                    possible_answer='['+str(questions[i]['validations']['min_value'])+','+str(questions[i]['validations']['max_value'])+']'
                    question_DS.append([id,id,title,possible_answer,type])   


                elif type=='opinion_scale':
                    if questions[i]['properties']['start_at_one']==True:
                        min_val=0
                    else:
                        min_val=1
                    possible_answer='['+str(min_val)+','+str(questions[i]['properties']['steps']-1)+']'
                    question_DS.append([id,id,title,possible_answer,type])  


                elif type=='long_text':
                    possible_answer=None
                    question_DS.append([id,id,title,possible_answer,type]) 


                elif type=='website':
                    possible_answer='http://'
                    question_DS.append([id,id,title,possible_answer,type])   


                elif type=='short_text':
                    possible_answer=None
                    question_DS.append([id,id,title,possible_answer,type]) 


                elif type=='email':
                    possible_answer=None
                    question_DS.append([id,id,title,possible_answer,type])   


                elif type=='dropdown':
                    choices=[u['label'] for u in questions[i]['properties']['choices']] 
                    for j in range(len(choices)):
                        id2=id+'_'+str(j)
                        possible_answer=choices[j]
                        question_DS.append([id,id2,title,possible_answer,type])


                elif type=='multiple_choice':
                    choices=[u['label'] for u in questions[i]['properties']['choices']] 
                    if questions[i]['properties']['allow_multiple_selection']==True:
                        type='multiple_choice_choices'
                    else:
                        type='multiple_choice_1_choice'
                    for j in range(len(choices)):
                        id2=id+'_'+str(j)
                        possible_answer=choices[j]
                        question_DS.append([id,id2,title,possible_answer,type])


                    if questions[i]['properties']['allow_other_choice']==True:
                        possible_answer='autre_text'
                        question_DS.append([id,id,title,possible_answer,type])


            print("We create the answers list")
            rep_DS=[]
            for i in range(len(reponses)):
                if i % 100 == 0:
                    print(str(i)+"th form out of "+str(len(reponses)))

                rep_user_DS=[]
                rep_user=reponses[i]['answers']
                
                if 'userid' in reponses[i]['hidden'].keys():
                    uuid=reponses[i]['hidden']['userid']
                    if uuid[0]=='"':
                        uuid=uuid2.UUID(reponses[i]['hidden']['userid'][1:-1])
                    elif uuid=='xxxxx':
                        uuid=None
                    else:
                        uuid=uuid2.UUID(reponses[i]['hidden']['userid'])
                else:
                    uuid=None
                    
                if 'email' in reponses[i]['hidden'].keys():
                    email=reponses[i]['hidden']['email'][1:-1]
                else:
                    email=None
                    
                date=time.mktime(pd.to_datetime(reponses[i]['submitted_at']).timetuple())
                token=reponses[i]['token']
                id_quest=[t['field']['id'] for t in rep_user]

                for j in range(len(question_DS)):
                    id=question_DS[j][1]
                    if question_DS[j][0] in id_quest:
                        rep_quest=[t for t in rep_user if t['field']['id']==question_DS[j][0]][0]

                        if rep_quest['field']['type'] in ['short_text','long_text']:
                            rep=rep_quest['text']
                            rep_DS+=[[id,email,uuid,token,date,1,rep]]

                        elif rep_quest['field']['type'] in ['legal','yes_no']:
                            rep=1 if rep_quest['boolean']==True else 0
                            rep_DS+=[[id,email,uuid,token,date,rep,None]]

                        elif rep_quest['field']['type']=='date':
                            rep=rep_quest['date']   
                            rep_DS+=[[id,email,uuid,token,date,1,rep]]

                        elif rep_quest['field']['type'] in ['number','opinion_scale','rating']:
                            rep=rep_quest['number']  
                            rep_DS+=[[id,email,uuid,token,date,rep,None]]

                        elif rep_quest['field']['type']=='website':
                            rep=rep_quest['url']  
                            rep_DS+=[[id,email,uuid,token,date,1,rep]]

                        elif rep_quest['field']['type']=='email':
                            rep=rep_quest['email']  
                            rep_DS+=[[id,email,uuid,token,date,1,rep]]

                        elif rep_quest['field']['type']=='dropdown':
                            if question_DS[j][3]==rep_quest['text']:
                                rep_DS+=[[id,email,uuid,token,date,rep,None]] 
                            else:
                                rep_DS+=[[id,email,uuid,token,date,rep,None]]


                        elif rep_quest['field']['type']=='multiple_choice':

                            if question_DS[j][4]=='multiple_choice_1_choice':
                                choix='choice'
                            else:
                                choix='choices'

                            if id!=question_DS[j][0]:
                                if question_DS[j][3] in rep_quest[choix]:
                                    rep_DS+=[[id,email,uuid,token,date,1,None]] 
                                else:
                                    rep_DS+=[[id,email,uuid,token,date,0,None]]

                            else:
                                if 'other'in rep_quest[choix].keys():
                                    rep=rep_quest[choix]['other']  
                                    rep_DS+=[[id,email,uuid,token,date,1,rep]]
                                else:
                                    rep_DS+=[[id,email,uuid,token,date,0,None]] 

                    else:
                        rep_DS+=[[id,email,uuid,token,date,None,None]]

            print("It's good")            
            return(question_DS,rep_DS)