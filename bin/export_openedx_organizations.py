"""
Export Open edX organizations to a YAML file.
The YAML file will be used by the deployment process to update the Open edX Site Configuration.

Warn: if you execute this script too much times, your Open edX LMS account could be locked for
30 minutes.

Example:
    python3 nau-data/bin/export_openedx_organizations.py --user <email> --password <password> \
        --lms lms.nau.edu.pt --output nau-data/envs/<env>/group_vars/all/23_organizations.yml
"""
import requests
import argparse
import yaml
import sys


def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--user", "--email", required=True, help="Your some user email")
    argParser.add_argument("--password", "--pass", required=True, help="Your some user password")
    argParser.add_argument("--lms", required=True, help="Your LMS domain")
    argParser.add_argument("--output", nargs='?', type=argparse.FileType('w'),
                    default=sys.stdout, help="Your organization yaml output file")

    args = argParser.parse_args()
    user_email = args.user
    user_password = args.password
    lms_domain = args.lms
    output = args.output

    # print(user_email)
    # print(user_password)
    # print(lms_domain)

    lms_url = f"https://{lms_domain}"

    # get up to 1000 organizations at once, so we don't need to iterate
    page_size = 1000

    session = requests.Session()
    login = session.get(f'{lms_url}/login')
    auth_r = session.post(
        f'{lms_url}/api/user/v1/account/login_session/',
        data={
            "email": user_email,
            "password": user_password,
        },
        headers={
            "X-CSRFToken": login.cookies.get("csrftoken"),
            "referer": f'{lms_url}/login',
        },
    )
    if not auth_r.ok:
        response = str(auth_r)
        raise RuntimeError(f'Invalid login, check your user/pass arguments {response}')

    api_result = session.get(
        f'{lms_url}/api/organizations/v0/organizations/?page_size={page_size}',
    )

    # read reponse as json
    api_result_dict=api_result.json()

    # define the output converted dict
    organization_logos_config = {}

    # iterate each organization received on the API call
    results = api_result_dict.get('results')
    for organization in results:
        org_code = organization.get('short_name')
        org_logo = organization.get('logo')
        organization_logos_config[org_code]={
            'alt': org_code,
            'src': org_logo,
        }

    # write
    org_export = {'NAU_HEADER_ORGANIZATION_LOGOS': organization_logos_config}
    yaml.dump(org_export, output)

# call
main()
