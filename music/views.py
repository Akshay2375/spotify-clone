from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import auth
# Create your views here.
import requests
from django.http import JsonResponse



# def search_artists(request):
#     query=request.GET.get('q','')
#     if not query:
#         return JsonResponse({'error': 'Please provide an artist name.'}, status=400)
    
    
#     params={'query':query,'limit':10}
#     url = 'https://discoveryprovider.audius.co/v1/users/search'
#     try:
#         response=requests.get(url,params=params)
#         data = response.json()
#         return JsonResponse(data)
#     except Exception as e:
#          return JsonResponse({'error': str(e)}, status=500)

# def search_tracks(request):
#     query = request.GET.get('q', 'drake')
#     url = f'https://discoveryprovider.audius.co/v1/tracks/search'
#     params = {'query': query, 'limit': 10}
#     response=requests.get(url, params=params)
#     response_data=response.json()
    

# audius_api/views.py
import requests
from django.http import JsonResponse

# Keep the same function name for template use
def top_artists():
    url = 'https://discoveryprovider.audius.co/v1/tracks/trending?limit=30'
    try:
        response = requests.get(url)
        data = response.json().get('data', [])
        
        artists = {}
        for track in data:
            user = track.get('user')
            if not user:
                continue
            artist_id = user.get('id')
            if artist_id not in artists:
                artists[artist_id] = {
                    'id': artist_id,
                    'name': user.get('name', 'No Name'),
                    'profile_picture': user.get('profile_picture', {}).get('150x150')
                }
        
        
        return list(artists.values())
    
    except Exception as e:
        print("Error fetching top artists:", e)
        return []

    
    
    
import requests

def top_tracks():
    url = 'https://discoveryprovider.audius.co/v1/tracks/trending?limit=18'
    try:
        response = requests.get(url)
        data = response.json().get('data', [])
        track_details = {}

        for track in data:
            track_id = track.get('id')
            track_name = track.get('title', 'Unknown Title')
            user = track.get('user')  # safely get user dictionary
            duration = track.get('duration', 0)
            duration = format_duration(duration)
            # Get artist name
            track_artist = user.get('name', 'No Name') if user else 'Unknown Artist'

            # Safely get artwork
            artwork = track.get('artwork', {})
            cover_image = artwork.get('150x150', 'https://via.placeholder.com/150')

            track_details[track_id] = {
                'id': track_id,
                'name': track_name,
                'artist': track_artist,
                'cover_image': cover_image,
                'duration':duration
            }

        return list(track_details.values())

    except Exception as e:
        print("Error fetching top tracks:", e)
        return []
    
def format_duration(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def music(request, pk):
    # Fetch track directly from Audius (more reliable)
    url = f"https://discoveryprovider.audius.co/v1/tracks/{pk}"
    response = requests.get(url)
    data = response.json().get("data")

    if not data:
        return render(request, "404.html", {"message": "Track not found"})

    artist = data.get("user", {}).get("name", "Unknown Artist")
    title = data.get("title", "Unknown Title")
    artwork = data.get("artwork", {}).get("150x150", "https://via.placeholder.com/150")
    duration = format_duration(data.get("duration", 0))
    audio_url = f"https://discoveryprovider.audius.co/v1/tracks/{pk}/stream"

    context = {
        "artist_name": artist,
        "track_name": title,
        "cover_image": artwork,
        "audio_url": audio_url,
        "duration": duration,
    }

    return render(request, "music.html", context)

 
def index(request):
    artist_info = top_artists()   
    top_track_list=top_tracks()
    chunk_size = 6
    chunked_tracks = [
        top_track_list[i:i + chunk_size] 
        for i in range(0, len(top_track_list), chunk_size)
    ]

    context = {
        'artist_info': artist_info,
        'chunked_tracks': chunked_tracks,   
    }
    
    return render(request, 'index.html',context )


def profile(request,pk):
    
    base_url='https://discoveryprovider.audius.co/v1'
    # Get Artist Data
    url=f"{base_url}/users/{pk}"
    artist_response=requests.get(url)
    artist_data=artist_response.json().get('data',{})
    
    
    # get all traak by artist
    track_url=f"{base_url}/users/{pk}/tracks"
    track_response=requests.get(track_url)
    tracks_data=track_response.json().get('data',[])
    
    
    profile_photo = artist_data.get("profile_picture", {}).get("1000x1000", "")
    followers = artist_data.get("follower_count", 0)

    tracks_clean=[]
    for track in tracks_data:
      
     track_image=track.get("artwork",{}).get("150x150","https://via.placeholder.com/150")
     if not track_image:
         continue
     duration=track.get("duration", 0)
     formatted_duration = format_duration(duration)
     tracks_clean.append({
            "title": track.get("title"),
            "artwork": track_image,
            "duration": formatted_duration
        })
    context = {
         "artist": artist_data,
        "tracks": tracks_clean,
        "profile_photo": profile_photo,
        "followers": followers,
        
    }
    
    
    
    return render(request,'profile.html',context)

import requests
from django.shortcuts import render

def search(request):
    base_url = 'https://discoveryprovider.audius.co/v1'
    results = []

    # Get query and type from GET parameters
    search_query = request.GET.get('search_query', '')
    search_type = request.GET.get('type', 'tracks')

    if search_query:
        if search_type == 'artists':
            url = f"{base_url}/users/search?query={search_query}"
        else:
            url = f"{base_url}/tracks/search?query={search_query}"

        try:
            response = requests.get(url)
            results = response.json().get('data', [])
        except Exception as e:
            print("Error fetching search results:", e)

    context = {
        'query': search_query,
        'results': results,
        'search_type': search_type,
    }

    return render(request, "search.html", context)


def login(request):
    if request.method=='POST':
        username=request.POST.get('username') 
        password=request.POST.get('password')
        user=auth.authenticate(username=username,password=password)
        
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            messages.info(request,'invalid credentials')
            return redirect('login')
    
    return render(request,'login.html')




def signup(request):
    
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        password2=request.POST['password2']
        
        if password==password2:
            if User.objects.filter(email=email).exists():
               messages.info(request,'email Taken')
               return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request,'Username Taken') 
                return redirect('signup')
            else:
                user=User.objects.create_user(username=username,email=email,password=password)    
                user.save()
                user_login=auth.authenticate(username=username,password=password)
                auth.login(request,user_login)
                return redirect('/')
        else:
            messages.info(request,'Password not matching')
            return redirect('signup')
    
    else:
     return render(request,'signup.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')
  
  
  
