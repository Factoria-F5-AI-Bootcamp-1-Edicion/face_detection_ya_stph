from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import StreamingHttpResponse
from accounts.forms import RegistrationForm
from accounts.forms import LoginForm
from .models import UserProfile
import face_recognition
# import requests
import cv2
import numpy as numpy
from PIL import Image as img, ImageDraw
import fnmatch
import os

# Used for finding dir paths
# rootDir = '../facialrecognition'

IMAGES_DIR = 'facialrecognition/media/images'
VERIF_DIR = 'facialrecognition/media/verif'

user_photo = []
user_photo_name = []


def home(request):
    return render(request, 'accounts/home.html')


def login(request):
    context = {}
    global userLoginName
    global users
    if request.method == "POST":
        form = LoginForm(request.POST, request.FILES)
        if form.is_valid():
            userName = form.cleaned_data.get("username")
            userLoginName = userName
            users = UserProfile.objects.filter(
                title=userLoginName)  # If the username matches a name in the database move to verify photo
            if users:
                return render(request, 'accounts/verifyLogin.html', context)

            else:
                form = LoginForm()
                errorMessage = "Error: invalid Username please try again"  # else return error message
                context = {'form': form, 'errorMessage': errorMessage, }
                return render(request, 'accounts/login.html', context)
    else:
        form = LoginForm()
        context['form'] = form
        return render(request, 'accounts/login.html', context)


# Fully working adding users and images
def register(request):
    context = {}
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            img = form.cleaned_data.get("images")
            errorname = UserProfile.objects.filter(title=name)
            if errorname:
                errorMessage = "Error: username already exists"  # else return error message
                context = {'form': form, 'errorMessage': errorMessage, }
                return render(request, 'accounts/register.html', context)
            else:
                obj = UserProfile.objects.create(
                    title=name,
                    img=img
                )
                obj.save()
                print(obj)
                return render(request, 'accounts/home.html', context)

    else:
        form = RegistrationForm()
    context['form'] = form
    return render(request, 'accounts/register.html', context)


def verifyPhoto(request):
    context = {}
    # DEBUG CODE TO FIND DIRECTORY TREES
    # for dirName, subdirList, fileList in os.walk(rootDir):
    #     print('Found directory: %s' % dirName)
    #     for fname in fileList:
    #         print('\t%s' % fname)

    '''Loop over images in directory, add to lists
    '''
    print("Loading registered faces database!")
    for file in os.listdir(IMAGES_DIR):
        if file.endswith(('.jpg', '.jpeg', '.png')):
            image = face_recognition.load_image_file(f"{IMAGES_DIR}/{file}")
            name_face_encoding = face_recognition.face_encodings(image)
            if len(name_face_encoding) > 0:
                # encodes all found faces
                encoding = name_face_encoding[0]
                # add encodings to list
                user_photo.append(encoding)
                # add photo name to list
                user_photo_name.append(file)

                # DEBUG print
                print(user_photo)
                print(user_photo_name)

            else:
                print("¡No se detectó un área de cara válida!")
                pass
            continue

    '''Decides where user is redirected based on return of takePhoto()
    if true - redirect to login
    if false - redirect to register
    '''

    if takePhotoLogin() is True:
        form = LoginForm()
        context = {'form': form,
                   'users': users,
                   }

        return render(request, 'accounts/loggedIn.html', context)
    else:
        form = LoginForm()
        context['form'] = form

        return redirect('/login')

def takePhotoLogin():
    context = {}
    # Get user to take image
    capture = cv2.VideoCapture(0)
    # Create live feed to take image and save photo
    while True:
        ret, frame = capture.read()
        cv2.imshow("Take Verification picture", frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')):
            cv2.imwrite(f"{VERIF_DIR}/photo.png", frame)
            break
    capture.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    # load the image
    ver_photo = face_recognition.load_image_file(f"{VERIF_DIR}/photo.png")
    # encode the image
    ver_photo_enc = face_recognition.face_encodings(ver_photo)[0]

    # DEBUG print
    print(f"VERIFICATION PHOTO: {ver_photo}")
    print(f"VERIFICATION PHOTO ENC: {ver_photo_enc}")

    # get locations of loaded verification photo used for comparison
    ver_locs = face_recognition.face_locations(ver_photo)
    # find faces and encodings
    ver_photo_enc = face_recognition.face_encodings(ver_photo, ver_locs)

    # check if the verification photo matches a user photo
    for (top, right, bottom, left), ver_photo_enc in zip(ver_locs, ver_photo_enc):
        matches = face_recognition.compare_faces(user_photo, ver_photo_enc)

    # return results
    if True in matches:
        print("Thank you for logging in")
        return True
    else:
        print("FAILED")
        return False
