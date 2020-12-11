from odoo import models, api, fields


class WhatsappSendMessage(models.TransientModel):

    _name = 'whatsapp.message.wizard'
    _description = 'send whatsapp message to opportunity'

    user_id = fields.Char(string="Recipient", required=True)
    phone = fields.Char(string="Phone", required=True)
    message = fields.Text(string="message", required=True)

    def send_message(self):
        if self.message and self.phone:
            message_string = ''
            message = self.message.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone="+self.phone+"&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
            }