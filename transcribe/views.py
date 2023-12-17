from django.shortcuts import render, redirect
from .forms import UploadForm
from django.http import FileResponse, HttpResponse
from django.contrib import messages

import os
import uuid
from django.shortcuts import render
from pytube import YouTube
import shutil
import whisper

# importing libraries 
import speech_recognition as sr 
import os 
from pydub import AudioSegment
from pydub.silence import split_on_silence

from googletrans import Translator, LANGUAGES

import os
import uuid

from django.http import FileResponse
from django.shortcuts import get_object_or_404

from django.contrib.auth.models import User 
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

from transcribe.models import UserDetail
from .models import UserDetail

from user_payment.models import Transaction
from django.utils import timezone
from datetime import datetime

def download_file(request, file_path):
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response

def handle_uploaded_file(audio_file):
    unique_id = str(uuid.uuid4())
    local_directory_path = os.path.join("transcribe_files/local_directory", unique_id)
    os.makedirs(local_directory_path, exist_ok=True)

    with open(os.path.join(local_directory_path, audio_file.name), 'wb+') as destination:
        for chunk in audio_file.chunks():
            destination.write(chunk)
    return os.path.join(local_directory_path, audio_file.name)


def signup(request):
    if request.method=='POST':
        uname=request.POST.get('username')
        email=request.POST.get('email')
        pass1=request.POST.get('password1')
        pass2=request.POST.get('password2')

        if pass1!=pass2:
            return HttpResponse("Your password and confirm password are not Same!!")
        else:
            my_user=User.objects.create_user(uname,email,pass1)
            my_user.save()
            return redirect('LoginPage')
    return render (request,'signup.html')

def LoginPage(request):
    if request.method=='POST':
        username=request.POST.get('username')
        pass1=request.POST.get('pass')
        user=authenticate(request,username=username,password=pass1)
        if user is not None:
            login(request,user)
            return redirect('/upload')
        else:
            return HttpResponse ("Username or Password is incorrect!!!")
    return render (request,'login.html')

def LogoutPage(request):
    if request.user.is_authenticated:        
        logout(request)
        messages.success(request, "logged out Successfully")
    return redirect('LoginPage')

def translate(text, target_lang):
    translator = Translator()
    translated_text = translator.translate(text, dest=target_lang)
    return translated_text.text


# @login_required(login_url='login')
def upload(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                youtube_url = form.cleaned_data['YouTube_URL']
                local_directory = form.cleaned_data['local_directory']
                video_language = form.cleaned_data['video_language']
                
                if youtube_url:
                    uploaded_filename = youtube_url
                    video_name = YouTube(youtube_url).title
                if local_directory:
                    uploaded_filename = local_directory
                    video_name = local_directory

        ###############################################################################
        #               storing data to database
        ###############################################################################
                transactions = Transaction.objects.filter(user=request.user)
                for transaction in transactions:
                    transaction.remaining_transaction -= 1
                    if transaction.remaining_transaction < 1:
                        return HttpResponse("you dont have enough credentials. Please subscribe the Plan! ")
                    
                    
                    print(transaction.plan_expire_on)
                    now_with_offset = datetime.now(timezone.utc).astimezone()
                    formatted_datetime = now_with_offset.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                    datetime_object = datetime.strptime(formatted_datetime, "%Y-%m-%d %H:%M:%S.%f%z")
                    if transaction.plan_expire_on < datetime_object:
                        return HttpResponse("your plan is expired. Please subscribe the Plan")
                    transaction.save()

                

                user_detail = UserDetail(
                    user=request.user,  # Assuming the currently logged-in user is the uploader
                    video_name=video_name,  # You should replace this with the actual video name
                    youtube_link_or_filename=uploaded_filename,  # Assuming youtube_url is the link
                    language=video_language,
                    status="processing",  # Set an initial status
                    # files="work in Progress"  # Set the file path to the text file
                )

                # Save the instance to the database
                user_detail.save()
                ##################################################################
                print(video_language)

                if youtube_url:
                    print("this is YT ")
                    #################################################################
                    #               downloading Youtube vido
                    #################################################################
                    yt = YouTube(youtube_url)
                    # video_stream = yt.streams.get_highest_resolution()
                    audio_stream = yt.streams.get_audio_only()

                    unique_id = str(uuid.uuid4())
                    download_path = os.path.join("transcribe_files/downloaded_YT_videos", unique_id)
                    os.makedirs(download_path, exist_ok=True)

                    video_download_path = download_path

                    # Download the video and audio streams to the specified directory
                    # video_stream.download(output_path=download_path, filename="video.mp4")
                    audio_stream.download(output_path=download_path, filename="audio")
                    print("Download completed successfully.")


                    

                    ##########################################################
                    #           converting audio file to text file
                    ##########################################################
                    input_audio_file = os.path.join(video_download_path, 'audio')
                    model = whisper.load_model("base")
                    result = model.transcribe(input_audio_file)
                    text = result["text"]
                    segments = result["segments"]
                    ##########################################################
                                    # Create VTT file
                    ##########################################################
                    vtt_content = "WEBVTT\n\n"
                    for i, segment in enumerate(segments):
                        start_time = segment["start"]
                        end_time = segment["end"]
                        # vtt_content += f"{i+1}\n{start_time} --> {end_time}\n{segment['text']}\n\n"
                        if video_language=="en":
                            vtt_content += f"{start_time} --> {end_time}\n{segment['text']}\n\n"
                        else:
                            vtt_content += f"{start_time} --> {end_time}\n{translate(segment['text'],video_language)}\n\n"

                    vtt_file_path = os.path.join(video_download_path, 'audio.vtt')
                    with open(vtt_file_path, 'w') as vtt_file:
                        vtt_file.write(vtt_content)

                    ##########################################################
                                    # Create SRT file
                    ##########################################################
                    srt_content = ""
                    for i, segment in enumerate(segments):
                        start_time = "{:02}:{:02}:{:02},{:03}".format(
                            int(segment["start"])//3600, int(segment["start"])//60%60,
                            int(segment["start"])%60, int((segment["start"] - int(segment["start"])) * 1000)
                        )
                        end_time = "{:02}:{:02}:{:02},{:03}".format(
                            int(segment["end"])//3600, int(segment["end"])//60%60,
                            int(segment["end"])%60, int((segment["end"] - int(segment["end"])) * 1000)
                        )
                        if video_language=="en":
                            srt_content += f"{i+1}\n{start_time} --> {end_time}\n{segment['text']}\n\n"
                        else:
                            srt_content += f"{i+1}\n{start_time} --> {end_time}\n{translate(segment['text'], video_language)}\n\n"
                        

                    srt_file_path = os.path.join(video_download_path, 'audio.srt')
                    with open(srt_file_path, 'w') as srt_file:
                        srt_file.write(srt_content)

                    ##########################################################
                                    #creating TXT file
                    ##########################################################
                    
                    text_file_path = os.path.join(video_download_path, 'audio.txt')
                    with open(text_file_path, 'w') as text_file:
                        if video_language=="en":
                            text_file.write(text)
                        else:
                            text_file.write(translate(text, video_language))
                    # print("Text file created successfully:", text_file_path)
                    # return render(request, 'success.html', {'text_file_path': text_file_path})
                    ##################################################################
            

                    # return redirect('success_page') 

                if local_directory:
                    print("this is local_directory")
                    file_directory_path = handle_uploaded_file(local_directory) #file downloaded in localdirectory

                    model = whisper.load_model("base")
                    result = model.transcribe(file_directory_path)
                    text = result["text"]
                    segments = result["segments"]

                    # Specify the path where you want to save the text file
                    directory_path = file_directory_path.split("/")[:-1]
                    directory_path = "/".join(directory_path)
                    ##########################################################
                                    #creating VTT file
                    ##########################################################
                    vtt_content = "WEBVTT\n\n"
                    for i, segment in enumerate(segments):
                        start_time = segment["start"]
                        end_time = segment["end"]
                        # vtt_content += f"{i+1}\n{start_time} --> {end_time}\n{segment['text']}\n\n"
                        if video_language=="en":
                            vtt_content += f"{start_time} --> {end_time}\n{segment['text']}\n\n"
                        else:
                            vtt_content += f"{start_time} --> {end_time}\n{translate(segment['text'],video_language)}\n\n"


                    vtt_file_path = os.path.join(directory_path, 'audio.vtt')
                    with open(vtt_file_path, 'w') as text_file:
                        text_file.write(vtt_content)
                    ##########################################################
                                    #creating SRT file
                    ##########################################################
                    srt_content = ""
                    for i, segment in enumerate(segments):
                        start_time = "{:02}:{:02}:{:02},{:03}".format(
                            int(segment["start"])//3600, int(segment["start"])//60%60,
                            int(segment["start"])%60, int((segment["start"] - int(segment["start"])) * 1000)
                        )
                        end_time = "{:02}:{:02}:{:02},{:03}".format(
                            int(segment["end"])//3600, int(segment["end"])//60%60,
                            int(segment["end"])%60, int((segment["end"] - int(segment["end"])) * 1000)
                        )
                        if video_language=="en":
                            srt_content += f"{i+1}\n{start_time} --> {end_time}\n{segment['text']}\n\n"
                        else:
                            srt_content += f"{i+1}\n{start_time} --> {end_time}\n{translate(segment['text'], video_language)}\n\n"

                    srt_file_path = os.path.join(directory_path, 'audio.srt')
                    with open(srt_file_path, 'w') as text_file:
                        text_file.write(srt_content)

                    ##########################################################
                                    #creating TXT file
                    ##########################################################
                    text_file_path = os.path.join(directory_path, 'audio.txt')
                    with open(text_file_path, 'w') as text_file:
                        if video_language=="en":
                            text_file.write(result["text"])
                        else:
                            text_content = translate(result["text"], video_language)
                            text_file.write(text_content)


                # Assuming you have file paths like this:
                # VTT_File = vtt_file_path
                # SRT_File = srt_file_path
                # TXT_FIle = text_file_path

                # file_paths = [
                #     vtt_file_path,
                #     srt_file_path,
                #     text_file_path
                # ]
                user_detail.files = {}
                ##########################################################################
                #                      Update & upload the data to the database
                ##########################################################################
                user_detail.status = "finished"

                # Assign file paths with labels
                user_detail.VTT_file_Path = vtt_file_path
                user_detail.SRT_file_Path = srt_file_path
                user_detail.TXT_file_Path = text_file_path
                # user_detail.files = file_paths

                # Save the instance to the database
                user_detail.save()
                ###############################################################################


                print("Text file created successfully:", text_file_path)
                # return render(request, 'success.html', {'text_file_path': text_file_path})
                return redirect('user_details')
        else:
            form = UploadForm()
        return render(request, 'upload.html', {'form': form, 'loader':"processing"})
    else:
        return redirect('LoginPage')



def user_details_view(request):
    user_details = UserDetail.objects.filter(user=request.user).order_by('-date')
    return render(request, 'user_details.html', {'user_details': user_details})


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from transcribe.models import UserDetail

def delete_user_details(request, id):
    if request.method == 'GET':
        if request.user.is_authenticated:
            user_detail = get_object_or_404(UserDetail, id=id, user=request.user)
            user_detail.delete()
            # return JsonResponse({'status': 'success'})
            return redirect('user_details')
        else:
            user_details = UserDetail.objects.filter(user=request.user).order_by('-date')
    return render(request, 'user_details.html', {'user_details': user_details})


