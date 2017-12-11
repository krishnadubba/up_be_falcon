import os
import sys
import json
import pickle
import requests
import random

ROOT_DIR = os.path.dirname(os.path.dirname(sys.path[0]))
sys.path.append(ROOT_DIR)

def get_n_random_users(n):
    random_users_url = 'https://randomuser.me/api/?results=%d' %n
    users_data = requests.get(random_users_url)
    return json.loads(users_data.text)['results']
    
def get_n_uggipuggi_random_users(n, user_data_file=None, user_pics_dir=None):
    if os.path.isfile(user_data_file):
        uggi_puggi_users = pickle.load(open(user_data_file, 'rb'))
        assert len(uggi_puggi_users) >= n
        return uggi_puggi_users[:n]
    else:    
        if not os.path.isdir(user_data_file):
            user_pics_dir = os.path.join(ROOT_DIR, 'test_data', 'user_pics')
        
        uggi_puggi_users = []
        user_data = get_n_random_users(n)
        for user in user_data:
            display_name = user['login']['username']
            first_name   = user['name']['first']
            last_name    = user['name']['last']
            gender       = user['gender']
            email        = user['login']['username'] + '@uggipuggi.com' #user['email'].replace('\\','')
            phone        = user['phone'].replace('-','')
            country      = user['nat']
            
            display_pic_filename = os.path.join(user_pics_dir, display_name + '.jpg')
            f = open(display_pic_filename, 'wb')
            f.write(requests.get(user['picture']['large']).content)
            f.close()
            display_pic = display_pic_filename
            uggi_puggi_users.append({"display_name": display_name,
                                     "display_pic": display_pic,
                                     "first_name": first_name,
                                     "last_name": last_name,
                                     "email": email,
                                     "gender": gender,
                                     "phone": phone,
                                     "country": country
                                    })
        with open(user_data_file, 'wb') as pickle_file:    
            pickle.dump(uggi_puggi_users, pickle_file)
        return uggi_puggi_users

if __name__ == "__main__":
    users = get_n_uggipuggi_random_users(50, user_data_file='/tmp/uggipuggi_test_users.p')
    #print (users)