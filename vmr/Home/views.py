from django.shortcuts import render,redirect
from .forms import VideoForm
from . models import *
import os
import cv2
import numpy as np
import time
import tensorflow as tf
import tensorflow_hub as hub
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout

# Global Variables
PATH = 'media/media/'
MODEL = hub.load('model')
N_FRAMES = None
USED_FRAMES = None

FRAME_LIMITER = 8
FPS = None
FRAME_COUNT = None
TOTAL_SECONDS = None

BATCH_SIZE = 32
N_FILES = 0
RESIZE = (256,256)

# Create your views here.
def home(request):
	user=request.user
	if user.is_authenticated:
		return render(request,'Home/index.html',{'user':user})
	else:
		return render(request,'Home/login.html')

def signup(request):
	if request.method == 'POST':
		username = request.POST['username']
		email = request.POST['email']
		password = request.POST['password']
		confirm_password = request.POST['confirm_password']
		
		# Check if passwords match
		if password == confirm_password:
			if not User.objects.filter(username=username).exists():
				# Create a new user
				user = User.objects.create_user(username=username, email=email, password=password)
				user.save()
				messages.success(request, 'Account created successfully! You can now log in.')
				user = authenticate(request, username=username, password=password)
				login(request, user)
				return redirect('home') 
			else:
				messages.error(request, 'Username already exists. Please choose a different username.')
		else:
			messages.error(request, 'Passwords do not match. Please try again.')
			
	return render(request, 'Home/signup.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'Home/login.html')

def user_logout(request):
	user=request.user
	if not user.is_authenticated:
		return render(request,'Home/login.html')
	else:
		logout(request)
		messages.success(request, 'Logged out successfully.')
		return redirect('login') 

def contact(request):
	user=request.user
	if request.method == 'POST':
		name = request.POST['name']
		email = request.POST['email']
		message = request.POST['message']
		
		contact = Contact(name=name, email=email, message=message)
		contact.save()
		messages.success(request, 'Your message has been sent. Thank you for contacting us!')
		return redirect('contact')

	if user.is_authenticated:
		return render(request,'Home/contact.html',{'user':user})
	else:
		return render(request,'Home/login.html')
	
def sports_analysis(request):
	return render(request,'Home/sports.html')

def video_editing_assistant(request):
	return render(request,'Home/video_editing.html')

def security_footage_analysis(request):
	return render(request,'Home/security_footage.html')

def media_monitoring(request):
	return render(request,'Home/media_monitoring.html')

def get_archive(request):
	current_user = request.user

	if current_user.is_authenticated:
		user_archives = Archive.objects.filter(user=current_user)
		return render(request,'Home/archive.html',{'archives':user_archives})
	else:
		return render(request,'Home/login.html')		

def upload_video(request):
	global FPS,FRAME_COUNT,TOTAL_SECONDS,N_FRAMES, USED_FRAMES

	if request.method == 'POST':
		form = VideoForm(request.POST,request.FILES)
		if form.is_valid():
			uploaded_file = form.cleaned_data['video_file']
			print(uploaded_file)
			print(dir(uploaded_file))
			file_name = uploaded_file.name
			
			import shutil
			if os.path.exists(PATH+'video_data'):
				shutil.rmtree(PATH)
			Video.objects.all().delete()
			
			form.save()		
			FPS,FRAME_COUNT,TOTAL_SECONDS,N_FRAMES, USED_FRAMES = load_and_save(file_name)
			return render(request,'Home/operations.html',{'video_name':file_name})
	else:
		form = VideoForm()
	return render(request,'Home/index.html',{'form':form})

# def results(request):
# 	# timestamps = get_timestamps(,"1000")
# 	return render(request,'Home/results.html',{'timestamps':timestamps})



#EDITED
def analyze(request):
	print(request.user)
	video = Video.objects.all()
	total_videos = len(video)
	video_file = str(video[total_videos-1].video_file).split('/')[-1]

	if request.method == 'POST':
		text = request.POST['query']
		query=np.array([text])
		print(text)
		print(query)
		print("Getting results..")
		scores = get_results(query)
		print("Got results..")

		print("Getting timestamps..")
		timestamps = get_timestamps(scores)
		print("Got timestamps..")

		###
		archive = Archive(user = request.user, timestamp = timestamps[0], vid_name = video_file)
		archive.save()
		###

		return render(request,'Home/results.html',{'query_out':query,'video_name':video_file,'timestamps':timestamps})
	else:
		return render(request,'Home/operations.html',{'video_name':video_file})
	
def load_and_save(video_url, batch_size= BATCH_SIZE,resize = RESIZE, frame_limiter = FRAME_LIMITER):
	global N_FILES
	path = PATH+video_url
	cap = cv2.VideoCapture(path)

	n_frames = 0
	file_no = 0
	frames = []


	dir_path = os.path.join(PATH,'video_data')
	os.mkdir(dir_path)

	
	fps = cap.get(cv2.CAP_PROP_FPS)
	frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
	print(frame_count, fps)
	seconds = frame_count / fps
	
	
	used_frames = 0
	try:
		while True:
			ret, frame = cap.read()
			if not ret:
				break

			n_frames+=1
			if n_frames%frame_limiter == 0:
				frame = crop_center_square(frame)
				frame = cv2.resize(frame, resize)
				frame = frame[:, :, [2, 1, 0]]
				frame = frame/255.0
				frames.append(frame)
				used_frames+=1

			if len(frames) == batch_size:
				file_name = "f"+str(file_no)
				file_no+=1
				save_path = os.path.join(dir_path,file_name)
				with open(save_path, 'wb') as f:
					np.save(f, frames)
				frames = []
	finally:
		cap.release()
	if len(frames)>0:
		if len(frames)<batch_size:
			extra_frames = batch_size-len(frames)
			frames+=(frames[-1]*extra_frames)
		file_name = "f"+str(file_no)
		file_no+=1
		save_path = os.path.join(dir_path,file_name)
		with open(save_path, 'wb') as f:
			np.save(f, frames)
		frames = []
	N_FILES = file_no+1

	return fps, frame_count, seconds, n_frames, used_frames

def crop_center_square(frame):
	y, x = frame.shape[0:2]
	min_dim = min(y, x)
	start_x = (x // 2) - (min_dim // 2)
	start_y = (y // 2) - (min_dim // 2)
	return frame[start_y:start_y+min_dim,start_x:start_x+min_dim]

def generate_embeddings(model, input_frames, input_words):
	vision_output = model.signatures['video'](tf.constant(tf.cast(input_frames, dtype=tf.float32)))
	text_output = model.signatures['text'](tf.constant(input_words))
	return vision_output['video_embedding'], text_output['text_embedding']

def get_results(query):
  	# cwd = os.getcwd()
	dir_path = os.path.join(PATH,'video_data')
	n_files = len(os.listdir(dir_path))
	scores = []
	for file_no in range(n_files-1):
		print("file: ",file_no)
		file_name = "f"+str(file_no)
		file_path = os.path.join(dir_path,file_name)
		f = np.load(file_path)
		f = np.array([f])
		video_embd, text_embd = generate_embeddings(MODEL, f, query)
		score = np.dot(text_embd, tf.transpose(video_embd))
		scores.append(score)

	return np.array(scores)	


#EDITED
def get_timestamps(scores):
	global N_FILES,TOTAL_SECONDS,FRAME_LIMITER,FPS,TOTAL_SECONDS
	print(TOTAL_SECONDS,FRAME_LIMITER,FPS)
	scores=np.array(scores)
	scores=scores.flatten()
	print(scores)
	top_indices = scores.argsort()[-5:][::-1]
	print(top_indices)
	batch_duration = TOTAL_SECONDS/N_FILES
	timestamps = []

	for idx in top_indices:
		start_sec = int(idx*batch_duration)
		end_sec = start_sec+10
		start_minutes = int(start_sec / 60)
		start_rem_sec = int(start_sec % 60)
		end_minutes = int(end_sec / 60)
		end_rem_sec = int(end_sec % 60)
		start_time_stamp = f"{start_minutes}:{start_rem_sec}"
		end_time_stamp = f"{end_minutes}:{end_rem_sec}"
		timestamps.append(start_time_stamp+" - "+end_time_stamp)

	return timestamps

	



