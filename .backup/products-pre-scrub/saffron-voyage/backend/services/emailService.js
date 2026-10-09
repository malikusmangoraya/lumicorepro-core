class EmailService {
  static async sendNotification(to, subject, text) {
    console.log(`[EmailService] Notification to ${to}: ${subject}`);
    return true;
  }
}

module.exports = EmailService;
