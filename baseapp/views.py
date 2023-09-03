from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .forms import AdminRegistrationForm, UserLoginForm, AppointmentForm, AppointmentRequestForm, AppointmentResponseForm, MessageForm
from django.contrib.auth.decorators import login_required
from .models import *
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime, timedelta, date



# Create your views here.


#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#####
def homePage(request):
    categories = ConsultancyCategories.objects.all()
    context = {'categories' : categories}
    return render(request, 'baseapp/homePage.html', context)

def signUp(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User Registration Succesful...")
            return redirect("home")
        else:
            messages.error(request, "Registration Unsuccessful, Invalid Credentials Entered!!")
    else:
        form = UserRegistrationForm()

    context = {'form' : form}
    return render(request, 'accounts/registerPage.html', context)


def signIn(request):
    if request.method == 'POST':
        form = UserLoginForm(request, request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, "Congratulations, you are now logged in....")
                return redirect("home")
            else:
                messages.error(request, "Invalid Credentials Entered..Try again Later!!")

        else:
            messages.error(request, "Invalid Username or Password used....Try again Later!!!")
    else:
        form = UserLoginForm()
    context = {'form' : form}
    return render(request, 'accounts/loginPage.html', context)

      
def signOut(request):
    logout(request)
    messages.info(request, "Successfully Logged out!!")
    return redirect("login")


def profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    context = {'profile' : profile}
    return render(request, 'accounts/userProfile.html', context)


def consultantServices(request, username):
    services = ConsultancyService.objects.filter(consultant__username=username)
    context = {'services': services}
    return render(request, 'baseapp/consultantServices.html', context)


def consultancyServiceDetail(request, serviceID):
    service = get_object_or_404(ConsultancyService, id=serviceID)
    if request.method == 'POST':
        ConsultationRequest.objects.create(
            client=request.user,
            consultant=service.consultant,
            service=service
        )
        return redirect('profile', username=request.user.username)
    context = {'service' : service}
    return render(request, 'baseapp/serviceDetail.html', context)


def consultationRequest(request):
    consultationRequests = ConsultationRequest.objects.filter(consultant=request.user)
    context = {'consultationRequests' : consultationRequests}
    return render(request, 'baseapp/consultationRequests.html', context)


def acceptDeclineRequest(request, requestID, action):
    consultationRequest = get_object_or_404(ConsultationRequest, id=requestID)
    if action == 'accept':
        consultationRequest.requestStatus = 'accepted'
        consultationRequest.save()
    elif action == 'decline':
        consultationRequest.requestStatus = 'declined'
        consultationRequest.save()
    return redirect('consultation_request')


def consultantsList(request):
    consultants = Consultant.objects.all()
    context = {'consultants' : consultants}
    return render(request, 'baseapp/consultants_list.html', context)


def consultant_detail(request, consultant_id):
    consultant = get_object_or_404(Consultant, id=consultant_id)
    context = {'consultant' : consultant}
    return render(request, 'baseapp/consultant_detail.html', context)


def scheduleAppointment(request, consultant_id):
    consultant = get_object_or_404(Consultant, id=consultant_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.consultant = consultant
            appointment.save()

            return redirect('appointment_confirmation')
    else:
        form = AppointmentForm()
    context = {'form' : form, 'consultant' : consultant}
    return render(request, 'baseapp/schedule_appointment.html', context)


def manageAppointments(request):
    appointments = Appointment.objects.filter(client=request.user.client)
    context = {'appiontments' : appointments}
    return render(request, 'baseapp/manage_appiontments.html', context)


def cancelAppointment(request, appointment_id):
    appiontment = get_object_or_404(Appointment, id=appointment_id)

    if request.user.client == appiontment.client:
        appiontment.delete()

    return redirect('manage_appiontments')


def clientDashboard(request):
    client = request.user.client
    appiontments = Appointment.objects.filter(client=client)
    context = {'client' : client, 'appointments' : appiontments}
    return render(request, 'baseapp/client_dashboard.html', context)


def sendMessage(request, reciever_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        reciever = User.objects.get(id=reciever_id)
        message = Message.objects.create(sender=request.user, reciever=reciever, content=content)
        message.save()

        notification = Notification.objects.create(user=reciever, message=f'You have a New Message from {request.user}')
        notification.save()

        return redirect('inbox')



def inbox(request):
    recieved_messages = Message.objects.filter(reciever=request.user)
    context = {'messages' : recieved_messages}
    return render(request, 'baseapp/inbox.html', context)



def notifications(request):
    notifcations =Notification.objects.filter(user=request.user).order_by('-timestamp')
    context = {'notifications' : notifcations}
    return render(request, 'baseapp/notifications.html', context)


def mark_notifications_as_read(request, notifcation_id):
    try:
        notification = Notification.objects.get(id=notifcation_id, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        return JsonResponse({'status' : 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status' : 'error'}, status=404)


def request_appointment(request, consultant_id):
    consultant = User.objects.get(id=consultant_id)
    
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        if form.is_valid():
            # Your appointment request logic here...
            
            # Create a notification for the consultant
            message = f"A client has requested an appointment with you."
            notification = Notification(user=consultant, message=message)
            notification.save()
            
            return redirect('appointment_request_confirmation')  # Redirect to a confirmation page
    else:
        form = AppointmentRequestForm()
    
    return render(request, 'consultancy/request_appointment.html', {'form': form, 'consultant': consultant})



def respond_appointment_request(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    client = appointment.client
    
    if request.method == 'POST':
        form = AppointmentResponseForm(request.POST)
        if form.is_valid():
            response = form.cleaned_data['response']
            
            # Update the appointment status
            appointment.status = response
            appointment.save()
            
            # Create a notification for the client
            message = f"Your appointment request has been {response}."
            notification = Notification(user=client, message=message)
            notification.save()
            
            return redirect('appointment_response_confirmation')  # Redirect to a confirmation page
    else:
        form = AppointmentResponseForm()
    
    return render(request, 'consultancy/respond_appointment_request.html', {'form': form, 'appointment': appointment})



def respond_to_client(request, client_id):
    client = User.objects.get(id=client_id)
    
    if request.method == 'POST':
        response_message = request.POST['response_message']  # Adjust this based on your form
        # Your response logic here...

        # Create a notification for the client
        message = f"A response has been received from the consultant: {response_message}"
        notification = Notification(user=client, message=message)
        notification.save()

        return redirect('response_confirmation')  # Redirect to a confirmation page

    return render(request, 'consultancy/respond_to_client.html', {'client': client})



def send_message(request, recipient_id):
    recipient = User.objects.get(id=recipient_id)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            
            # Create a notification for the recipient
            notification = Notification(user=recipient, message=message)
            notification.save()
            
            return redirect('message_sent_confirmation')  # Redirect to a confirmation page
    else:
        form = MessageForm()
    
    return render(request, 'consultancy/send_message.html', {'form': form, 'recipient': recipient})


def appointmentConfirmation(request):
    return render(request, 'baseapp/appointment_confirmation.html')


# def mark_notifications_as_read(request, notiifcation_id):
#     notification = Notification.objects.get(id=notiifcation_id)
#     notification.is_read = True
#     notification.save()
#     return redirect('notifications')

# def notiifcations(request):
#     user = request.user
#     notifcations = Notification.objects.filter(user=user)
#     context = {'notifications' : notifcations}
#     return render(request, 'baseapp/notifications.html', context)


# def notificationsMessageCount(request):
#     user = request.user
#     notiifcationCount = Notification.objects.filter(user=user, read=False).count()
#     messageCount = Message.objects.filter(recipient=user).count()

#     return JsonResponse({
#         'notification_count' : notiifcationCount,
#         'message_count' : messageCount
#     })


# def loadMessages(request, recipient_username):
#     sender = request.user
#     recipient = User.objects.get(username=recipient_username)
#     messages = Message.objects.filter(
#         (models.Q(sender=sender) & models.Q(recipient=recipient)) | 
#         (models.Q(sender=recipient) & models.Q(recipient=sender))
#     )

#     messages_data = [{'content' : message.messsageContent, 'sender' : message.sender.username} for message in messages]
#     return JsonResponse({'messages' : messages_data})



# def messaging(request, recipientUsername):
#     sender = request.user
#     recipient = get_object_or_404(User, username=recipientUsername)
#     if request.method == 'POST':
#         messageContent = request.POST.get('messageContent')
#         Message.objects.create(sender=sender, recipient=recipient, messageContent=messageContent)
#         return redirect('messaging', recipientUsername=recipientUsername)
#     messages = Message.objects.filter(sender=sender, recipient=recipient) | Message.objects.filter(sender=recipient, recipient=sender)
#     messages = messages.order_by('timestamp')

#     context = {'recipient' : recipient, 'messages' : messages}
#     return render(request, 'baseapp/messaging.html', context)


# def sendMessage(request):
#     if request.method == 'POST':
#         sender = request.user
#         recipientusername = request.POST.get('recipient')
#         recipient = get_object_or_404(User, username=recipientusername)
#         messageContent = request.POST.get('messageContent')
#         Message.objects.create(sender=sender, recipient=recipient, messageContent=messageContent)
#         return JsonResponse({'success' : True})
#     return JsonResponse({'success' : False})




    









