"""
Email service using SendGrid for sending OTPs and notifications
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "libraryai110@gmail.com")
        if not self.api_key:
            print("⚠️  WARNING: SENDGRID_API_KEY not found in environment variables")
        self.sg = SendGridAPIClient(self.api_key) if self.api_key else None
    
    def send_otp_email(self, to_email: str, otp: str) -> bool:
        """
        Send OTP email to user
        
        Args:
            to_email: Recipient email address
            otp: 6-digit OTP code
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.sg:
            print("❌ SendGrid client not initialized. Check API key.")
            return False
            
        try:
            print(f"📧 Attempting to send OTP to {to_email}...")
            print(f"   From: {self.from_email}")
            print(f"   OTP: {otp}")
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject='Your LibraryAI OTP Code',
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            <h2 style="color: #333; text-align: center;">LibraryAI Verification Code</h2>
                            <p style="color: #666; font-size: 16px;">Hello,</p>
                            <p style="color: #666; font-size: 16px;">Your One-Time Password (OTP) for LibraryAI is:</p>
                            <div style="text-align: center; margin: 30px 0;">
                                <span style="font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 5px; padding: 15px 30px; border: 2px dashed #4CAF50; display: inline-block; border-radius: 5px;">
                                    {otp}
                                </span>
                            </div>
                            <p style="color: #666; font-size: 14px;">This OTP will expire in <strong>5 minutes</strong>.</p>
                            <p style="color: #666; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">This is an automated message from LibraryAI. Please do not reply.</p>
                        </div>
                    </body>
                </html>
                """
            )
            
            response = self.sg.send(message)
            print(f"✅ Email sent successfully! Status: {response.status_code}")
            return response.status_code in [200, 201, 202]
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error sending OTP email: {error_msg}")
            
            # Check for common SendGrid errors
            if "403" in error_msg or "Forbidden" in error_msg:
                print("⚠️  SENDGRID ERROR: Sender email not verified!")
                print(f"   Please verify '{self.from_email}' in SendGrid:")
                print("   1. Go to https://app.sendgrid.com/settings/sender_auth/senders")
                print("   2. Click 'Create New Sender'")
                print(f"   3. Verify the email: {self.from_email}")
                print("   4. Check your inbox for verification email")
            elif "401" in error_msg or "Unauthorized" in error_msg:
                print("⚠️  SENDGRID ERROR: Invalid API key!")
                print("   Please check your SENDGRID_API_KEY in .env file")
            
            import traceback
            traceback.print_exc()
            return False
    
    def send_borrow_confirmation(self, to_email: str, user_name: str, book_title: str, 
                                 borrow_date: str, due_date: str) -> bool:
        """
        Send book borrow confirmation email
        
        Args:
            to_email: Student email
            user_name: Student name
            book_title: Title of borrowed book
            borrow_date: Borrow date
            due_date: Return due date
            
        Returns:
            bool: True if sent successfully
        """
        if not self.sg:
            print("❌ SendGrid client not initialized. Check API key.")
            return False
            
        try:
            print(f"📧 Sending borrow confirmation to {to_email}...")
            print(f"   Book: {book_title}")
            print(f"   Due Date: {due_date}")
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f'Book Borrowed: {book_title}',
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            <h2 style="color: #333; text-align: center;">📚 Book Borrowed Successfully</h2>
                            <p style="color: #666; font-size: 16px;">Hi {user_name},</p>
                            <p style="color: #666; font-size: 16px;">You have successfully borrowed the following book:</p>
                            
                            <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                                <h3 style="color: #333; margin-top: 0;">{book_title}</h3>
                                <p style="color: #666; margin: 5px 0;"><strong>Borrow Date:</strong> {borrow_date}</p>
                                <p style="color: #666; margin: 5px 0;"><strong>Due Date:</strong> {due_date}</p>
                            </div>
                            
                            <p style="color: #666; font-size: 14px;">Please return the book by the due date to avoid late fees.</p>
                            <p style="color: #666; font-size: 14px;">Happy reading! 📖</p>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">LibraryAI - Your Digital Library Assistant</p>
                        </div>
                    </body>
                </html>
                """
            )
            
            response = self.sg.send(message)
            print(f"✅ Borrow confirmation email sent! Status: {response.status_code}")
            return response.status_code in [200, 201, 202]
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error sending borrow confirmation: {error_msg}")
            
            if "11002" in error_msg or "getaddrinfo failed" in error_msg:
                print("⚠️  NETWORK ERROR: Cannot reach SendGrid servers")
                print("   Possible causes:")
                print("   1. No internet connection")
                print("   2. Firewall blocking outbound HTTPS")
                print("   3. DNS resolution failure")
                print("   Solution: Check your internet connection and firewall settings")
            elif "403" in error_msg or "Forbidden" in error_msg:
                print(f"⚠️  Email '{self.from_email}' not verified in SendGrid")
                print("   Go to: https://app.sendgrid.com/settings/sender_auth/senders")
            
            return False
            return False
    
    def send_due_date_reminder(self, to_email: str, user_name: str, book_title: str, 
                               due_date: str) -> bool:
        """
        Send due date reminder email (1 day before)
        
        Args:
            to_email: Student email
            user_name: Student name
            book_title: Title of borrowed book
            due_date: Return due date
            
        Returns:
            bool: True if sent successfully
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f'Reminder: Book Due Tomorrow - {book_title}',
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            <h2 style="color: #FF9800; text-align: center;">⚠️ Book Due Tomorrow</h2>
                            <p style="color: #666; font-size: 16px;">Hi {user_name},</p>
                            <p style="color: #666; font-size: 16px;">This is a friendly reminder that the following book is due <strong>tomorrow</strong>:</p>
                            
                            <div style="background-color: #fff3e0; padding: 20px; border-left: 4px solid #FF9800; margin: 20px 0;">
                                <h3 style="color: #333; margin-top: 0;">{book_title}</h3>
                                <p style="color: #666; margin: 5px 0;"><strong>Due Date:</strong> {due_date}</p>
                            </div>
                            
                            <p style="color: #666; font-size: 14px;">Please return the book by tomorrow to avoid late fees.</p>
                            <p style="color: #666; font-size: 14px;">If you need more time, please contact the library.</p>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">LibraryAI - Your Digital Library Assistant</p>
                        </div>
                    </body>
                </html>
                """
            )
            
            response = self.sg.send(message)
            return response.status_code in [200, 201, 202]
        
        except Exception as e:
            print(f"Error sending due date reminder: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
