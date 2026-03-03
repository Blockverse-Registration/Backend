import razorpay
import hashlib
import hmac
import requests
import qrcode
from io import BytesIO

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.db import transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Team, Player


client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


@api_view(["POST"])
def create_order(request):
    team_type = request.data.get("team_type")

    if not team_type:
        return Response({"error": "Team type required"}, status=400)

    team_type = team_type.lower().strip()

    if team_type == "solo":
        amount = 20000
    elif team_type == "duo":
        amount = 35000
    else:
        return Response({"error": "Invalid team type"}, status=400)

    try:
        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        return Response({
            "id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
def verify_payment(request):
    razorpay_order_id = request.data.get("razorpay_order_id")
    razorpay_payment_id = request.data.get("razorpay_payment_id")
    razorpay_signature = request.data.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return Response(
            {"success": False, "message": "Missing payment fields"},
            status=400
        )

    body = razorpay_order_id + "|" + razorpay_payment_id

    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()

    if generated_signature != razorpay_signature:
        return Response(
            {"success": False, "message": "Invalid signature"},
            status=400
        )

    return Response({
        "success": True,
        "paymentId": razorpay_payment_id
    })


@api_view(["POST"])
def register_team(request):
    try:
        data = request.data
        payment_id = data.get("paymentId")
        captcha_token = data.get("captchaToken")

        if not payment_id:
            return Response(
                {"success": False, "message": "Missing payment ID"},
                status=400
            )

        captcha_response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": captcha_token
            },
            timeout=5
        ).json()

        if not captcha_response.get("success"):
            return Response(
                {"success": False, "message": "Invalid CAPTCHA"},
                status=400
            )

        if Team.objects.filter(payment_id=payment_id).exists():
            return Response({"success": True})

        if Team.objects.filter(team_id=data["teamId"]).exists():
            return Response(
                {"success": False, "message": "Team ID already exists"},
                status=400
            )

        plain_password = data["password"]

        with transaction.atomic():
            team = Team.objects.create(
                team_id=data["teamId"],
                team_type=data["team_type"],
                password=make_password(plain_password),
                payment_id=payment_id,
            )

            p1 = Player.objects.create(team=team, **data["player1"])

            if data["team_type"].lower() == "duo":
                p2 = Player.objects.create(team=team, **data["player2"])
                recipients = [p1.email, p2.email]
            else:
                recipients = [p1.email]

        response = Response({"success": True})

        try:
            qr_data = f"{team.team_id}|{payment_id}"
            qr = qrcode.make(qr_data)

            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)

            subject = "🎉 BlockVerse Registration Confirmed"

            html_content = f"""
            <h2>Registration Successful 🎉</h2>
            <p><b>Team ID:</b> {team.team_id}</p>
            <p><b>Password:</b> {plain_password}</p>
            <p>
            Please keep this information safe.<br>
            You will use Team ID and Password to register for contests.
            </p>
            <p>
            At the event, show the QR code below to mark your attendance.
            </p>
            """

            email = EmailMultiAlternatives(
                subject,
                "Registration successful",
                settings.DEFAULT_FROM_EMAIL,
                recipients,
            )

            email.attach_alternative(html_content, "text/html")

            email.attach(
                "BlockVerse_QR.png",
                buffer.getvalue(),
                "image/png"
            )

            email.send(fail_silently=False)

        except Exception as email_error:
            print("Email failed but registration saved:", email_error)

        return response

    except Exception as e:
        return Response(
            {"success": False, "message": str(e)},
            status=400
        )