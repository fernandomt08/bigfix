import traceback
import datetime
import requests
import logging
import logging.config
from os import path
import urllib3
import base64
import json
import time
import os
import re
import xml.etree.cElementTree as ET
import xml.dom.minidom

requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Logging Configuration
log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.ini')
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
logger = logging.getLogger(__name__)


usrname = os.environ['bf_user']
passwd = os.environ['bf_pass']
#URL for SandBox BigFix Environment
bigfixurl = "https://rootserver:52311/api"
bigfixsaurl = "https://saserver:8443/serverautomation"

#The full Server Automation REST XML Schema is available at: [https://saserver:8443/serverautomation/SA-REST.xsd]
#https://bigfix-wiki.hcltechsw.com/wikis/home?lang=en-us#!/wiki/BigFix%20Wiki/page/Plan

def list_automation_plans():

    """
    This function uses the general BigFix REST API to pull the list of automation plans and their details
    """
    endpoint = '/query?output=json&relevance='
    query = '(ids of it, names of it, name of site of it) of bes fixlets whose (exists mime field "plan-fixlet-children" of it And name of site of it contains "name custom site" AND name of it = "APITest")'

    r = requests.get(
        bigfixurl + endpoint + query,
        auth=(usrname, passwd), verify=False)

    logging.debug(r.url)
    if r.status_code == 200:
        json_plans = json.loads(r.text)
        for plan in json_plans['result']:
            logging.info(f'{plan[1]}')
            get_automation_plan_template(plan[0])
            logging.info('*********************')

def get_automation_plan_template(ap_id):
    """
    This action will query BigFix Server Automation to retrieve the information of Automation Plans.
    Retrieves the plan execution template XML document for the automation plan specified by the URL.
    To execute a plan, parameter and targeting information must be added to this template by the client.
    The completed template XML document may then be used to execute a plan by supplying it in the body of a POST to the same URL.

    The resource accessor URLs detailed below generally take the form:

    /serverautomation/{resource}/{site type}/{site name}/{object id}

    The individual URL components are:
    {resource} : Top level API resource, such as "plan" or "planaction".
    {site type}: May be one of: "master", "external", "operator" or "custom".
    {site name}: The name of the site containing an object to be located: e.g. "Server Automation".
    {object id}: The ID of an object located within the specified site, e.g. a plan fixlet or action.
    """
    query = '/plan/custom/name custom site/' + str(ap_id)
    r = requests.get(
        bigfixsaurl + query,
        auth=(usrname, passwd), verify=False)

    logging.debug(r.url)
    if r.status_code == 200:
        logging.info(r.text)
        return r.text


def create_bf_action(xml_body):
    '''
    This function will schedule the execution of an automation plan
    :param xml_body: The xml body of the automation plan
    :return: id of the action created

     Executes the automation plan specified by the URL using a supplied (and completed) plan execution template XML document.
    This template must include values for any parameters required by the plan, as well as targeting information for each step in the plan.

    '''
    query = '/plan/custom/name custom site/id of automation plan'
    r = requests.post(
        bigfixsaurl + query,
        auth=(usrname, passwd), data=xml_body, verify=False)


    if r.status_code == 200:
        logging.debug(r.text)
        return (str(r.text).strip())
    else:
        logging.info("There was an error sending the post request.")

def get_status_action(action_id):
    '''
    Retrieves the current state of the automation plan action specified by the URL,
    as well as the status of all step actions on the system created by the plan action.
    The information returned is comparable to that displayed on the Automation Plan Actions Status dashboard on the console

    Note: if the plan has already been completed/stopped/expired no results will be return.
    Details can be obtained by the normal BigFix REST API at this point too.
    '''

    query = '/planaction/' + action_id
    r = requests.get(
        bigfixsaurl + query,
        auth=(usrname, passwd), verify=False)
    logging.debug(r.url)
    if r.status_code == 200:
        logging.info(r.text)

if __name__ == "__main__":
    #list_automation_plans()

    # 125176 is the ID of the automation plan in BigFix, the IDs can be retrieved using the list_automation_plans function
    xml = get_automation_plan_template(125176)
    logging.info(xml)
    action_id = create_bf_action(xml)


    logging.info(f"Action ID: {action_id}")
    
