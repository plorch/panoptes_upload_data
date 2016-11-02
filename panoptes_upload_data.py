import csv
from panoptes_client import SubjectSet, Subject, Project, Panoptes

# TODO: put your username and password in here or use ENV vars
Panoptes.connect(username='UN', password='PW')

# get a ref to the project we're uploading to -> change this for the correct project
# e.g. https://www.zooniverse.org/projects/pat-lorch/cmp-wildlife-camera-traps
project = Project.find(slug='pat-lorch/cmp-wildlife-camera-traps')
# OR Just use the project id from the lab if you know it
# project = Project.find(PROJECT_ID_HERE)

# Debug check the workflows on the project
# for workflow in project.links.workflows:
#     print workflow.display_name

# EITHER create a new subject set linked to the project form above
# subject_set = SubjectSet()
# subject_set.links.project = project
# subject_set.display_name = 'Timbavati_Set'
# subject_set.save()

# OR find an existing subject set to add subject to
subject_set = SubjectSet.find(SUBJECT_SET_ID_HERE)

# empty list to add the saved subjects to the subject set
saved_subjects = []

# read the manifest and create externally linked subjects
# NOTE: TRY and to this in batches of 500 - 1000K images to avoid a failure
# not saving subject and linking to a subject set
with open('/PATH_TO_YOUR/manifest.csv', 'rb') as csvfile:
    subjects_to_upload = csv.DictReader(csvfile)
    for row in subjects_to_upload :
        # expected header format: image_name, origin, licence, link
        # print(row['image_name'], row['origin'], row['licence'], row['link'])

        # creat a new subject and set the metadata and the remote URL for the externally hosted images (not via zooniverse s3)
        subject = Subject()
        subject.links.project = project
        # TODO: change the image MIME type to match your data, png, etc
        subject.locations.append({'image/jpeg': row['link']})
        # TODO: You can set whatever metadata you want, or none at all
        subject.metadata['image_name'] = row['image_name']
        subject.metadata['origin'] = row['origin']
        subject.metadata['licence'] = row['licence']
        # handle api failures (network, etc)
        try:
            subject.save()
        except PanoptesAPIException:
            print('Error occurred, rolling back and cleaning up the created subjects.')
            for subject in saved_subjects :
                print('removing the subject with id: {}'.format(subject.id))
                # this method may change in the future, https://github.com/zooniverse/panoptes-python-client/issues/39
                Subject.delete(subject.id, headers={'If-Match': subject.etag})
            raise SystemExit

        # save in the list of subjects to add to the subject set above
        saved_subjects.append(subject)
        # add the subject to the subjet set 1 at a time.
        # but there is a more efficient way of adding this all at once (see below)
        # subject_set.add(subject)

# link the saved subjects to the subject set
# NOTE: this will only run after the whole file is processed and all subjects saved successfully
# try and keep the manifest set of data small enough to not have problems
# perhaps process large manifests in batches instead of all at once like i have it here
# happy to help out with this rather than have busted uploads to cleanup
subject_set.add(saved_subjects)
