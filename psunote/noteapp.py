import flask
import models
import forms

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"
models.init_app(app)

@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template("index.html", notes=notes)

@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if form.validate_on_submit():
        note = models.Note()
        form.populate_obj(note)
        note.tags = []  

        db = models.db
        for tag_name in form.tags.data:  
            tag = db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name)
            ).scalars().first()

            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            if tag not in note.tags:
                note.tags.append(tag)

        db.session.add(note)
        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-create.html", form=form)

@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalars().first()
    
    if not tag:
        return flask.abort(404)

    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html", tag=tag, tag_name=tag_name, notes=notes
    )


@app.route("/tags/delete/<int:id>", methods=["POST"], endpoint="tags_delete")
def tags_delete(id):
    db = models.db
    tag = db.session.execute(db.select(models.Tag).where(models.Tag.id == id)).scalars().first()

    if not tag:
        return flask.abort(404)

    db.session.execute(
        db.delete(models.note_tag_m2m).where(models.note_tag_m2m.c.tag_id == id)
    )

    db.session.delete(tag)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/notes/delete/<int:id>", methods=["POST"], endpoint="notes_delete")
def notes_delete(id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == id)).scalars().first()

    if not note:
        return flask.abort(404)

    db.session.delete(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route("/note/<int:id>/edit", methods=["GET", "POST"])
def notes_edit(id):
    note = models.Note.query.get(id)
    form = forms.NoteForm(obj=note)  

    if form.validate_on_submit():
        form.populate_obj(note)  
       
        note.tags = [] 
        db = models.db
        for tag_name in form.tags.data:
            tag = db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name)
            ).scalars().first()
            
            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            if tag not in note.tags:
                note.tags.append(tag)

        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-edit.html", form=form, note=note)

if __name__ == "__main__":
    app.run(debug=True)