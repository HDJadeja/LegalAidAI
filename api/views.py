from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import *
from django.views.decorators.csrf import csrf_exempt
from .chroma_client import *
from django.conf import settings
from .chroma_client import client
import os
import requests




@csrf_exempt 
@api_view(["POST"])
def signup(request):
    username = request.POST.get("uname")
    password = request.POST.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required."}, status=400)

    if LegalAdviceUser.objects.filter(username=username).exists():
        return Response({"error": "User already exists."}, status=200) 

    
    collection = client.create_collection(
        f"{username}_Collection",
        embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )

    user_created = LegalAdviceUser.objects.create(username=username, password=password)
    user_created.save()

    request.session["username"] = username
    request.session["chat_history"] = []

    return Response({"message": "User created successfully."}, status=201)


@csrf_exempt
@api_view(["POST"])
def login(request):
    username = request.POST.get("user")
    password_given = request.POST.get("password")
    print("----user is ",request.POST)
    user_object = LegalAdviceUser.objects.get(username=username)
    print(user_object)
    if user_object and user_object.password == password_given:
        request.session["username"] = username
        request.session["chat_history"] = []
        return Response({"message":"logged in "},status=200)
    else:
        return Response({"message":"incorrect Details","username":username},status=401)



@csrf_exempt
@api_view(["POST"])
def chat_llm(request):
    if request.session.get("username"):
        try:

            filenames = request.POST.get("filenames", "")
            filenames = filenames.split(",") if filenames else []

            query = request.POST.get('query')
            
            if not query:
                return Response({"error": "Query is required."}, status=400)
            llm_context = get_llm_context(query, request.session["username"], filenames)
            conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in request.session["chat_history"]])
            request.session["chat_history"].append({"role": "user", "content": query})


            API_KEY = settings.API_KEY
            LLM_MODEL = settings.MODEL
            url = settings.API_URL

            headers = {
                "Authorization": f"Bearer {API_KEY}", 
                "Content-Type": "application/json"
            }

            payload = {
                "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a legal assistant specializing in Indian law. Your primary responsibility is to assist users with queries related to constitutional law, criminal law, civil law, and procedural matters such as bail, trials, appeals, and related legal processes. Always prioritize the provided legal context when available, but supplement with general Indian legal principles when necessary. If a user asks any non-legal question, you must respond politely but firmly, stating that you are only authorized to assist with Indian legal matters."
                    )
                },
                {"role": "user", "content": f"Context:\n{llm_context['context']}\n\n{conversation_context}Question: {query}"}
                ], 
            "max_tokens": 500
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return Response(response.json()["choices"][0]["message"]["content"], status=200)
            else:
                return Response({"error": f"LLM request failed: {response.text}"}, status=response.status_code)
        except Exception as e:
            print(f"Error in chat_llm: {e}")
            return Response({"error": e}, status=500)
    else:
        return Response({"error": "Invalid request method or user not signed in.","redirect":"/login"}, status=405)





@api_view(['POST'])
def get_filenames(request):
    username = request.session.get("username")

    if not username:
        return Response({"error": "User not logged in"}, status=401)

    try:
        user = LegalAdviceUser.objects.get(username=username)
        user_files = LegalAdviceFile.objects.filter(user=user)
        filenames = [f.filename for f in user_files]
        return Response({"files": filenames})

    except LegalAdviceUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


@csrf_exempt
@api_view(['POST'])
def document_add(request):

    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=400)

    file = request.FILES['file']
    filename = file.name
    extension = os.path.splitext(filename)[1].lower()
    username = request.session.get("username")

    if not username:
        return Response({"error": "User not signed in"}, status=400)

    try:
        user = LegalAdviceUser.objects.get(username=username)
    except LegalAdviceUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    
    user_file = LegalAdviceFile.objects.create(user=user, file=file,filename=filename)
    file_path = user_file.file.path 
    collection_name = f"{username}_Collection"

    if extension == ".txt":
        process_txt(file_path,filename, collection_name,request.session["username"])
        return Response({"message": "Text file processed successfully."}, status=201)

    elif extension == ".pdf":
        process_pdf(file_path,filename, collection_name,request.session["username"])
        return Response({"message": "PDF file processed successfully."}, status=201)
    
    elif extension == ".docx":
        process_docx(file_path,filename, collection_name, request.session["username"])
        return Response({"message": "DOCX file processed successfully."}, status=201)

    else:
        return Response({"error": "Unsupported file type. Only PDF and TXT allowed."}, status=400)



