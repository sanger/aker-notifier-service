from .consts import *
from .notify import Notify


class Rule:
    """Class containing the rules to be executed for each type of event."""

    def __init__(self, env, config, message):
        """Init the class with the environment, config and message (event) to be checked."""
        self._env = env
        self._config = config
        self._message = message
        self._notify = Notify(self._env, self._config)

    def check_rules(self):
        """Check all the rules for the current message (event)."""
        if self._message.event_type == EVENT_SUB_CREATED:
            self._on_submission_create()
        elif self._message.event_type == EVENT_SUB_RECEIVED:
            self._on_submission_received()
        else:
            pass

    def _on_submission_create(self):
        """Notify once a submission has been created."""
        to, data, link = self._common_submission()
        data['user_identifier'] = self._message.user_identifier
        # Send a submission created email
        self._notify.send_email(subject=SBJ_SUB_CREATED,
                                from_address=self._config.email.from_address,
                                to=to,
                                template='submission_created',
                                data=data)
        # Send an email to the ethics officer
        if 'hmdmc_numbers' in self._message.metadata and self._message.metadata['hmdmc_numbers']:
            data['hmdmc_numbers'] = self._message.metadata['hmdmc_numbers']
            # Use the same link we have already created for the submission
            self._notify.send_email(subject=SBJ_SUB_CREATED_HMDMC,
                                    from_address=self._config.email.from_address,
                                    to=[self._config.contact.email_hmdmc_verify],
                                    template='submission_created_hmdmc',
                                    data=data)

    def _on_submission_received(self):
        """Notify once a submission has been received."""
        to, data, link = self._common_submission()
        if 'barcode' in self._message.metadata and self._message.metadata['barcode']:
            data['barcode'] = self._message.metadata['barcode']
        if 'created_at' in self._message.metadata and self._message.metadata['created_at']:
            data['created_at'] = self._message.metadata['created_at']
        if 'all_received' in self._message.metadata and self._message.metadata['all_received']:
            data['all_received'] = self._message.metadata['all_received']
        self._notify.send_email(subject=SBJ_SUB_RECEIVED,
                                from_address=self._config.email.from_address,
                                to=to,
                                template='submission_received',
                                data=data)

    def _common_submission(self):
        """Extract the common info for submission events."""
        link = ''
        data = {}
        to = [self._message.user_identifier]
        # Check if we can create a link
        if 'submission_id' in self._message.metadata and self._message.metadata['submission_id']:
            data['submission_id'] = self._message.metadata['submission_id']
            link = self._generate_link(PATH_SUBMISSION, self._message.metadata['submission_id'])
            data['link'] = link
        # Add the sample custodian to the to list
        if ('sample_custodian' in self._message.metadata
                and self._message.metadata['sample_custodian']):
            to.append(self._message.metadata['sample_custodian'])
        if 'deputies' in self._message.metadata and self._message.metadata['deputies']:
            for dep in self._message.metadata['deputies']:
                to.append(dep)
        return to, data, link

    def _generate_link(self, path, id):
        """Generate a link to the specific entity in the app provided by path."""
        return '{}://{}:{}/{}/{}'.format(self._config.link.protocol,
                                         self._config.link.root,
                                         self._config.link.port,
                                         path,
                                         id)
