from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets
from models import Tag  
import models


class TagListField(Field):
    widget = widgets.TextInput()

    def __init__(self, label="", validators=None, remove_duplicates=True, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.data = []

    def process_formdata(self, valuelist):
        data = []
        if valuelist:
            data = [x.strip() for x in valuelist[0].split(",")]

        if not self.remove_duplicates:
            self.data = data
            return

        self.data = []
        for d in data:
            if d not in self.data:
                self.data.append(d)

    def _value(self):
        if self.data:
            return ", ".join(str(tag) if isinstance(tag, str) else tag.name for tag in self.data)
        else:
            return ""


    def populate_obj(self, obj, name):
        tag_instances = []
        for tag_name in self.data:
            tag = Tag.query.filter_by(name=tag_name).first()

            if not tag: 
                tag = Tag(name=tag_name)
                models.db.session.add(tag)
            tag_instances.append(tag)

        setattr(obj, name, tag_instances)

BaseNoteForm = model_form(
    models.Note, base_class=FlaskForm, 
    exclude=["created_date", "updated_date"], 
    db_session=models.db.session
)

class NoteForm(BaseNoteForm):
    tags = TagListField("Tag")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, 'obj') and self.obj and self.obj.tags:
            self.tags.data = [tag.name for tag in self.obj.tags]