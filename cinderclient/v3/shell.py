# Copyright (c) 2013-2014 OpenStack Foundation
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import argparse
import collections
import os

from oslo_utils import strutils
import six

import cinderclient
from cinderclient import api_versions
from cinderclient import base
from cinderclient import exceptions
from cinderclient import shell_utils
from cinderclient import utils

from cinderclient.v2.shell import *  # flake8: noqa

FILTER_DEPRECATED = ("This option is deprecated and will be removed in "
                     "newer release. Please use '--filters' option which "
                     "is introduced since 3.33 instead.")


@api_versions.wraps('3.33')
@utils.arg('--resource',
           metavar='<resource>',
           default=None,
           help='Show enabled filters for specified resource. Default=None.')
def do_list_filters(cs, args):
        filters = cs.resource_filters.list(resource=args.resource)
        shell_utils.print_resource_filter_list(filters)


@utils.arg('--all-tenants',
           metavar='<all_tenants>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--all_tenants',
           nargs='?',
           type=int,
           const=1,
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help="Filters results by a name. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help="Filters results by a status. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--volume-id',
           metavar='<volume-id>',
           default=None,
           help="Filters results by a volume ID. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--volume_id',
           help=argparse.SUPPRESS)
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning backups that appear later in the backup '
                'list than that represented by this id. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of backups to return. Default=None.')
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.') % ', '.join(base.SORT_KEY_VALUES)))
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_backup_list(cs, args):
    """Lists all backups."""
    # pylint: disable=function-redefined

    search_opts = {
        'all_tenants': args.all_tenants,
        'name': args.name,
        'status': args.status,
        'volume_id': args.volume_id,
    }

    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))

    backups = cs.backups.list(search_opts=search_opts,
                              marker=args.marker,
                              limit=args.limit,
                              sort=args.sort)
    shell_utils.translate_volume_snapshot_keys(backups)
    columns = ['ID', 'Volume ID', 'Status', 'Name', 'Size', 'Object Count',
               'Container']
    if args.sort:
        sortby_index = None
    else:
        sortby_index = 0
    utils.print_list(backups, columns, sortby_index=sortby_index)


@utils.arg('--detail',
           action='store_true',
           help='Show detailed information about pools.')
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_get_pools(cs, args):
    """Show pool information for backends. Admin only."""
    # pylint: disable=function-redefined
    search_opts = {}
    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))
    if cs.api_version >= api_versions.APIVersion("3.33"):
        pools = cs.volumes.get_pools(args.detail, search_opts)
    else:
        pools = cs.volumes.get_pools(args.detail)
    infos = dict()
    infos.update(pools._info)

    for info in infos['pools']:
        backend = dict()
        backend['name'] = info['name']
        if args.detail:
            backend.update(info['capabilities'])
        utils.print_dict(backend)


RESET_STATE_RESOURCES = {'volume': utils.find_volume,
                         'backup': shell_utils.find_backup,
                         'snapshot': shell_utils.find_volume_snapshot,
                         'group': shell_utils.find_group,
                         'group-snapshot': shell_utils.find_group_snapshot}


@utils.arg('--group_id',
           metavar='<group_id>',
           default=None,
           help="Filters results by a group_id. Default=None."
                "%s" % FILTER_DEPRECATED,
           start_version='3.10')
@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--all_tenants',
           nargs='?',
           type=int,
           const=1,
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help="Filters results by a name. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help="Filters results by a status. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--bootable',
           metavar='<True|true|False|false>',
           const=True,
           nargs='?',
           choices=['True', 'true', 'False', 'false'],
           help="Filters results by bootable status. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--migration_status',
           metavar='<migration_status>',
           default=None,
           help="Filters results by a migration status. Default=None. "
                "Admin only. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--metadata',
           nargs='*',
           metavar='<key=value>',
           default=None,
           help="Filters results by a metadata key and value pair. "
                "Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--image_metadata',
           nargs='*',
           metavar='<key=value>',
           default=None,
           start_version='3.4',
           help="Filters results by a image metadata key and value pair. "
                "Require volume api version >=3.4. Default=None."
                "%s" % FILTER_DEPRECATED)
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning volumes that appear later in the volume '
                'list than that represented by this volume id. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of volumes to return. Default=None.')
@utils.arg('--fields',
           default=None,
           metavar='<fields>',
           help='Comma-separated list of fields to display. '
                'Use the show command to see which fields are available. '
                'Unavailable/non-existent fields will be ignored. '
                'Default=None.')
@utils.arg('--sort_key',
           metavar='<sort_key>',
           default=None,
           help=argparse.SUPPRESS)
@utils.arg('--sort_dir',
           metavar='<sort_dir>',
           default=None,
           help=argparse.SUPPRESS)
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.') % ', '.join(base.SORT_KEY_VALUES)))
@utils.arg('--tenant',
           type=str,
           dest='tenant',
           nargs='?',
           metavar='<tenant>',
           help='Display information from single tenant (Admin only).')
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_list(cs, args):
    """Lists all volumes."""
    # pylint: disable=function-redefined
    # NOTE(thingee): Backwards-compatibility with v1 args
    if args.display_name is not None:
        args.name = args.display_name

    all_tenants = 1 if args.tenant else \
        int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'project_id': args.tenant,
        'name': args.name,
        'status': args.status,
        'bootable': args.bootable,
        'migration_status': args.migration_status,
        'metadata': shell_utils.extract_metadata(args)
        if args.metadata else None,
        'glance_metadata': shell_utils.extract_metadata(args,
                                                        type='image_metadata')
        if hasattr(args, 'image_metadata') and args.image_metadata else None,
        'group_id': getattr(args, 'group_id', None),
    }
    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))

    # If unavailable/non-existent fields are specified, these fields will
    # be removed from key_list at the print_list() during key validation.
    field_titles = []
    if args.fields:
        for field_title in args.fields.split(','):
            field_titles.append(field_title)

    # --sort_key and --sort_dir deprecated in kilo and is not supported
    # with --sort
    if args.sort and (args.sort_key or args.sort_dir):
        raise exceptions.CommandError(
            'The --sort_key and --sort_dir arguments are deprecated and are '
            'not supported with --sort.')

    volumes = cs.volumes.list(search_opts=search_opts, marker=args.marker,
                              limit=args.limit, sort_key=args.sort_key,
                              sort_dir=args.sort_dir, sort=args.sort)
    shell_utils.translate_volume_keys(volumes)

    # Create a list of servers to which the volume is attached
    for vol in volumes:
        servers = [s.get('server_id') for s in vol.attachments]
        setattr(vol, 'attached_to', ','.join(map(str, servers)))

    if field_titles:
        # Remove duplicate fields
        key_list = ['ID']
        unique_titles = [k for k in collections.OrderedDict.fromkeys(
            [x.title().strip() for x in field_titles]) if k != 'Id']
        key_list.extend(unique_titles)
    else:
        key_list = ['ID', 'Status', 'Name', 'Size', 'Volume Type',
                    'Bootable', 'Attached to']
        # If all_tenants is specified, print
        # Tenant ID as well.
        if search_opts['all_tenants']:
            key_list.insert(1, 'Tenant ID')

    if args.sort_key or args.sort_dir or args.sort:
        sortby_index = None
    else:
        sortby_index = 0
    utils.print_list(volumes, key_list, exclude_unavailable=True,
                     sortby_index=sortby_index)


@utils.arg('entity', metavar='<entity>', nargs='+',
           help='Name or ID of entity to update.')
@utils.arg('--type', metavar='<type>', default='volume',
           choices=RESET_STATE_RESOURCES.keys(),
           help="Type of entity to update. Available resources "
                "are: 'volume', 'snapshot', 'backup', "
                "'group' (since 3.20) and "
                "'group-snapshot' (since 3.19), Default=volume.")
@utils.arg('--state', metavar='<state>', default=None,
           help=("The state to assign to the entity. "
                 "NOTE: This command simply changes the state of the "
                 "entity in the database with no regard to actual status, "
                 "exercise caution when using. Default=None, that means the "
                 "state is unchanged."))
@utils.arg('--attach-status', metavar='<attach-status>', default=None,
           help=('This is only used for a volume entity. The attach status '
                 'to assign to the volume in the database, with no regard '
                 'to the actual status. Valid values are "attached" and '
                 '"detached". Default=None, that means the status '
                 'is unchanged.'))
@utils.arg('--reset-migration-status',
           action='store_true',
           help=('This is only used for a volume entity. Clears the migration '
                 'status of the volume in the DataBase that indicates the '
                 'volume is source or destination of volume migration, '
                 'with no regard to the actual status.'))
def do_reset_state(cs, args):
    """Explicitly updates the entity state in the Cinder database.

    Being a database change only, this has no impact on the true state of the
    entity and may not match the actual state. This can render a entity
    unusable in the case of changing to the 'available' state.
    """
    # pylint: disable=function-redefined
    failure_count = 0
    single = (len(args.entity) == 1)

    migration_status = 'none' if args.reset_migration_status else None
    collector = RESET_STATE_RESOURCES[args.type]
    argument = (args.state,)
    if args.type == 'volume':
        argument += (args.attach_status, migration_status)

    for entity in args.entity:
        try:
            collector(cs, entity).reset_state(*argument)
        except Exception as e:
            print(e)
            failure_count += 1
            msg = "Reset state for entity %s failed: %s" % (entity, e)
            if not single:
                print(msg)

    if failure_count == len(args.entity):
        msg = "Unable to reset the state for the specified entity(s)."
        raise exceptions.CommandError(msg)


@utils.arg('size',
           metavar='<size>',
           nargs='?',
           type=int,
           action=CheckSizeArgForCreate,
           help='Size of volume, in GiBs. (Required unless '
                'snapshot-id/source-volid is specified).')
@utils.arg('--consisgroup-id',
           metavar='<consistencygroup-id>',
           default=None,
           help='ID of a consistency group where the new volume belongs to. '
                'Default=None.')
@utils.arg('--group-id',
           metavar='<group-id>',
           default=None,
           help='ID of a group where the new volume belongs to. '
                'Default=None.',
           start_version='3.13')
@utils.arg('--snapshot-id',
           metavar='<snapshot-id>',
           default=None,
           help='Creates volume from snapshot ID. Default=None.')
@utils.arg('--snapshot_id',
           help=argparse.SUPPRESS)
@utils.arg('--source-volid',
           metavar='<source-volid>',
           default=None,
           help='Creates volume from volume ID. Default=None.')
@utils.arg('--source_volid',
           help=argparse.SUPPRESS)
@utils.arg('--source-replica',
           metavar='<source-replica>',
           default=None,
           help='Creates volume from replicated volume ID. Default=None.')
@utils.arg('--image-id',
           metavar='<image-id>',
           default=None,
           help='Creates volume from image ID. Default=None.')
@utils.arg('--image_id',
           help=argparse.SUPPRESS)
@utils.arg('--image',
           metavar='<image>',
           default=None,
           help='Creates a volume from image (ID or name). Default=None.')
@utils.arg('--image_ref',
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Volume name. Default=None.')
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--display_name',
           help=argparse.SUPPRESS)
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Volume description. Default=None.')
@utils.arg('--display-description',
           help=argparse.SUPPRESS)
@utils.arg('--display_description',
           help=argparse.SUPPRESS)
@utils.arg('--volume-type',
           metavar='<volume-type>',
           default=None,
           help='Volume type. Default=None.')
@utils.arg('--volume_type',
           help=argparse.SUPPRESS)
@utils.arg('--availability-zone',
           metavar='<availability-zone>',
           default=None,
           help='Availability zone for volume. Default=None.')
@utils.arg('--availability_zone',
           help=argparse.SUPPRESS)
@utils.arg('--metadata',
           nargs='*',
           metavar='<key=value>',
           default=None,
           help='Metadata key and value pairs. Default=None.')
@utils.arg('--hint',
           metavar='<key=value>',
           dest='scheduler_hints',
           action='append',
           default=[],
           help='Scheduler hint, like in nova.')
@utils.arg('--allow-multiattach',
           dest='multiattach',
           action="store_true",
           help=('Allow volume to be attached more than once.'
                 ' Default=False'),
           default=False)
def do_create(cs, args):
    """Creates a volume."""

    # NOTE(thingee): Backwards-compatibility with v1 args
    if args.display_name is not None:
        args.name = args.display_name

    if args.display_description is not None:
        args.description = args.display_description

    volume_metadata = None
    if args.metadata is not None:
        volume_metadata = shell_utils.extract_metadata(args)

    # NOTE(N.S.): take this piece from novaclient
    hints = {}
    if args.scheduler_hints:
        for hint in args.scheduler_hints:
            key, _sep, value = hint.partition('=')
            # NOTE(vish): multiple copies of same hint will
            #             result in a list of values
            if key in hints:
                if isinstance(hints[key], six.string_types):
                    hints[key] = [hints[key]]
                hints[key] += [value]
            else:
                hints[key] = value
    # NOTE(N.S.): end of taken piece

    # Keep backward compatibility with image_id, favoring explicit ID
    image_ref = args.image_id or args.image or args.image_ref

    try:
        group_id = args.group_id
    except AttributeError:
        group_id = None

    volume = cs.volumes.create(args.size,
                               args.consisgroup_id,
                               group_id,
                               args.snapshot_id,
                               args.source_volid,
                               args.name,
                               args.description,
                               args.volume_type,
                               availability_zone=args.availability_zone,
                               imageRef=image_ref,
                               metadata=volume_metadata,
                               scheduler_hints=hints,
                               source_replica=args.source_replica,
                               multiattach=args.multiattach)

    info = dict()
    volume = cs.volumes.get(volume.id)
    info.update(volume._info)

    if 'readonly' in info['metadata']:
        info['readonly'] = info['metadata']['readonly']

    info.pop('links', None)
    utils.print_dict(info)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume for which to update metadata.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help='The action. Valid values are "set" or "unset."')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           end_version='3.14',
           help='Metadata key and value pair to set or unset. '
                'For unset, specify only the key.')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           start_version='3.15',
           help='Metadata key and value pair to set or unset. '
                'For unset, specify only the key(s): <key key>')
def do_metadata(cs, args):
    """Sets or deletes volume metadata."""
    volume = utils.find_volume(cs, args.volume)
    metadata = shell_utils.extract_metadata(args)

    if args.action == 'set':
        cs.volumes.set_metadata(volume, metadata)
    elif args.action == 'unset':
        # NOTE(zul): Make sure py2/py3 sorting is the same
        cs.volumes.delete_metadata(volume, sorted(metadata.keys(),
                                   reverse=True))


@api_versions.wraps('3.11')
def do_group_type_list(cs, args):
    """Lists available 'group types'. (Admin only will see private types)"""
    gtypes = cs.group_types.list()
    shell_utils.print_group_type_list(gtypes)


@api_versions.wraps('3.11')
def do_group_type_default(cs, args):
    """List the default group type."""
    gtype = cs.group_types.default()
    shell_utils.print_group_type_list([gtype])


@api_versions.wraps('3.11')
@utils.arg('group_type',
           metavar='<group_type>',
           help='Name or ID of the group type.')
def do_group_type_show(cs, args):
    """Show group type details."""
    gtype = shell_utils.find_gtype(cs, args.group_type)
    info = dict()
    info.update(gtype._info)

    info.pop('links', None)
    utils.print_dict(info, formatters=['group_specs'])


@api_versions.wraps('3.11')
@utils.arg('id',
           metavar='<id>',
           help='ID of the group type.')
@utils.arg('--name',
           metavar='<name>',
           help='Name of the group type.')
@utils.arg('--description',
           metavar='<description>',
           help='Description of the group type.')
@utils.arg('--is-public',
           metavar='<is-public>',
           help='Make type accessible to the public or not.')
def do_group_type_update(cs, args):
    """Updates group type name, description, and/or is_public."""
    is_public = strutils.bool_from_string(args.is_public)
    gtype = cs.group_types.update(args.id, args.name, args.description,
                                  is_public)
    shell_utils.print_group_type_list([gtype])


@api_versions.wraps('3.11')
def do_group_specs_list(cs, args):
    """Lists current group types and specs."""
    gtypes = cs.group_types.list()
    utils.print_list(gtypes, ['ID', 'Name', 'group_specs'])


@api_versions.wraps('3.11')
@utils.arg('name',
           metavar='<name>',
           help='Name of new group type.')
@utils.arg('--description',
           metavar='<description>',
           help='Description of new group type.')
@utils.arg('--is-public',
           metavar='<is-public>',
           default=True,
           help='Make type accessible to the public (default true).')
def do_group_type_create(cs, args):
    """Creates a group type."""
    is_public = strutils.bool_from_string(args.is_public)
    gtype = cs.group_types.create(args.name, args.description, is_public)
    shell_utils.print_group_type_list([gtype])


@api_versions.wraps('3.11')
@utils.arg('group_type',
           metavar='<group_type>', nargs='+',
           help='Name or ID of group type or types to delete.')
def do_group_type_delete(cs, args):
    """Deletes group type or types."""
    failure_count = 0
    for group_type in args.group_type:
        try:
            gtype = shell_utils.find_group_type(cs, group_type)
            cs.group_types.delete(gtype)
            print("Request to delete group type %s has been accepted."
                  % group_type)
        except Exception as e:
            failure_count += 1
            print("Delete for group type %s failed: %s" % (group_type, e))
    if failure_count == len(args.group_type):
        raise exceptions.CommandError("Unable to delete any of the "
                                      "specified types.")


@api_versions.wraps('3.11')
@utils.arg('gtype',
           metavar='<gtype>',
           help='Name or ID of group type.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help='The action. Valid values are "set" or "unset."')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='The group specs key and value pair to set or unset. '
                'For unset, specify only the key.')
def do_group_type_key(cs, args):
    """Sets or unsets group_spec for a group type."""
    gtype = shell_utils.find_group_type(cs, args.gtype)
    keypair = shell_utils.extract_metadata(args)

    if args.action == 'set':
        gtype.set_keys(keypair)
    elif args.action == 'unset':
        gtype.unset_keys(list(keypair))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='ID of tenant for which to set quotas.')
@utils.arg('--volumes',
           metavar='<volumes>',
           type=int, default=None,
           help='The new "volumes" quota value. Default=None.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='The new "snapshots" quota value. Default=None.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='The new "gigabytes" quota value. Default=None.')
@utils.arg('--backups',
           metavar='<backups>',
           type=int, default=None,
           help='The new "backups" quota value. Default=None.')
@utils.arg('--backup-gigabytes',
           metavar='<backup_gigabytes>',
           type=int, default=None,
           help='The new "backup_gigabytes" quota value. Default=None.')
@utils.arg('--consistencygroups',
           metavar='<consistencygroups>',
           type=int, default=None,
           help='The new "consistencygroups" quota value. Default=None.')
@utils.arg('--groups',
           metavar='<groups>',
           type=int, default=None,
           help='The new "groups" quota value. Default=None.',
           start_version='3.13')
@utils.arg('--volume-type',
           metavar='<volume_type_name>',
           default=None,
           help='Volume type. Default=None.')
@utils.arg('--per-volume-gigabytes',
           metavar='<per_volume_gigabytes>',
           type=int, default=None,
           help='Set max volume size limit. Default=None.')
def do_quota_update(cs, args):
    """Updates quotas for a tenant."""

    shell_utils.quota_update(cs.quotas, args.tenant, args)


@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume to snapshot.')
@utils.arg('--force',
           metavar='<True|False>',
           const=True,
           nargs='?',
           default=False,
           help='Enables or disables upload of '
           'a volume that is attached to an instance. '
           'Default=False. '
           'This option may not be supported by your cloud.')
@utils.arg('--container-format',
           metavar='<container-format>',
           default='bare',
           help='Container format type. '
                'Default is bare.')
@utils.arg('--container_format',
           help=argparse.SUPPRESS)
@utils.arg('--disk-format',
           metavar='<disk-format>',
           default='raw',
           help='Disk format type. '
                'Default is raw.')
@utils.arg('--disk_format',
           help=argparse.SUPPRESS)
@utils.arg('image_name',
           metavar='<image-name>',
           help='The new image name.')
@utils.arg('--image_name',
           help=argparse.SUPPRESS)
@utils.arg('--visibility',
           metavar='<public|private|community|shared>',
           help='Set image visibility to public, private, community or '
                'shared. Default=private.',
           default='private',
           start_version='3.1')
@utils.arg('--protected',
           metavar='<True|False>',
           help='Prevents image from being deleted. Default=False.',
           default=False,
           start_version='3.1')
def do_upload_to_image(cs, args):
    """Uploads volume to Image Service as an image."""
    volume = utils.find_volume(cs, args.volume)
    if cs.api_version >= api_versions.APIVersion("3.1"):
        shell_utils.print_volume_image(
            volume.upload_to_image(args.force,
                                   args.image_name,
                                   args.container_format,
                                   args.disk_format,
                                   args.visibility,
                                   args.protected))
    else:
        shell_utils.print_volume_image(
            volume.upload_to_image(args.force,
                                   args.image_name,
                                   args.container_format,
                                   args.disk_format))


@api_versions.wraps('3.9')
@utils.arg('backup', metavar='<backup>',
           help='Name or ID of backup to rename.')
@utils.arg('--name', nargs='?', metavar='<name>',
           help='New name for backup.')
@utils.arg('--description', metavar='<description>',
           help='Backup description. Default=None.')
def do_backup_update(cs, args):
    """Renames a backup."""
    kwargs = {}

    if args.name is not None:
        kwargs['name'] = args.name

    if args.description is not None:
        kwargs['description'] = args.description

    if not kwargs:
        msg = 'Must supply either name or description.'
        raise exceptions.ClientException(code=1, message=msg)

    shell_utils.find_backup(cs, args.backup).update(**kwargs)


@api_versions.wraps('3.7')
@utils.arg('--name', metavar='<name>', default=None,
           help='Filter by cluster name, without backend will list all '
                'clustered services from the same cluster. Default=None.')
@utils.arg('--binary', metavar='<binary>', default=None,
           help='Cluster binary. Default=None.')
@utils.arg('--is-up', metavar='<True|true|False|false>', default=None,
           choices=('True', 'true', 'False', 'false'),
           help='Filter by up/dow status. Default=None.')
@utils.arg('--disabled', metavar='<True|true|False|false>', default=None,
           choices=('True', 'true', 'False', 'false'),
           help='Filter by disabled status. Default=None.')
@utils.arg('--num-hosts', metavar='<num-hosts>', default=None,
           help='Filter by number of hosts in the cluster.')
@utils.arg('--num-down-hosts', metavar='<num-down-hosts>', default=None,
           help='Filter by number of hosts that are down.')
@utils.arg('--detailed', dest='detailed', default=False,
           help='Get detailed clustered service information (Default=False).',
           action='store_true')
def do_cluster_list(cs, args):
    """Lists clustered services with optional filtering."""
    clusters = cs.clusters.list(name=args.name, binary=args.binary,
                                is_up=args.is_up, disabled=args.disabled,
                                num_hosts=args.num_hosts,
                                num_down_hosts=args.num_down_hosts,
                                detailed=args.detailed)

    columns = ['Name', 'Binary', 'State', 'Status']
    if args.detailed:
        columns.extend(('Num Hosts', 'Num Down Hosts', 'Last Heartbeat',
                        'Disabled Reason', 'Created At', 'Updated at'))
    utils.print_list(clusters, columns)


@api_versions.wraps('3.7')
@utils.arg('binary', metavar='<binary>', nargs='?', default='cinder-volume',
           help='Binary to filter by.  Default: cinder-volume.')
@utils.arg('name', metavar='<cluster-name>',
           help='Name of the clustered service to show.')
def do_cluster_show(cs, args):
    """Show detailed information on a clustered service."""
    cluster = cs.clusters.show(args.name, args.binary)
    utils.print_dict(cluster.to_dict())


@api_versions.wraps('3.7')
@utils.arg('binary', metavar='<binary>', nargs='?', default='cinder-volume',
           help='Binary to filter by.  Default: cinder-volume.')
@utils.arg('name', metavar='<cluster-name>',
           help='Name of the clustered services to update.')
def do_cluster_enable(cs, args):
    """Enables clustered services."""
    cluster = cs.clusters.update(args.name, args.binary, disabled=False)
    utils.print_dict(cluster.to_dict())


@api_versions.wraps('3.7')
@utils.arg('binary', metavar='<binary>', nargs='?', default='cinder-volume',
           help='Binary to filter by.  Default: cinder-volume.')
@utils.arg('name', metavar='<cluster-name>',
           help='Name of the clustered services to update.')
@utils.arg('--reason', metavar='<reason>', default=None,
           help='Reason for disabling clustered service.')
def do_cluster_disable(cs, args):
    """Disables clustered services."""
    cluster = cs.clusters.update(args.name, args.binary, disabled=True,
                                 disabled_reason=args.reason)
    utils.print_dict(cluster.to_dict())


@api_versions.wraps('3.8')
@utils.arg('host',
           metavar='<host>',
           help='Cinder host on which to list manageable volumes; '
                'takes the form: host@backend-name#pool')
@utils.arg('--detailed',
           metavar='<detailed>',
           default=True,
           help='Returned detailed information (default true).')
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning volumes that appear later in the volume '
                'list than that represented by this reference. This reference '
                'should be json like. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of volumes to return. Default=None.')
@utils.arg('--offset',
           metavar='<offset>',
           default=None,
           help='Number of volumes to skip after marker. Default=None.')
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.'
                  ) % ', '.join(base.SORT_MANAGEABLE_KEY_VALUES)))
def do_manageable_list(cs, args):
    """Lists all manageable volumes."""
    # pylint: disable=function-redefined
    detailed = strutils.bool_from_string(args.detailed)
    volumes = cs.volumes.list_manageable(host=args.host, detailed=detailed,
                                         marker=args.marker, limit=args.limit,
                                         offset=args.offset, sort=args.sort)
    columns = ['reference', 'size', 'safe_to_manage']
    if detailed:
        columns.extend(['reason_not_safe', 'cinder_id', 'extra_info'])
    utils.print_list(volumes, columns, sortby_index=None)


@api_versions.wraps('3.13')
@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=utils.env('ALL_TENANTS', default=0),
           help='Shows details for all tenants. Admin only.')
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_group_list(cs, args):
    """Lists all groups."""
    search_opts = {'all_tenants': args.all_tenants}

    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))

    groups = cs.groups.list(search_opts=search_opts)

    columns = ['ID', 'Status', 'Name']
    utils.print_list(groups, columns)


@api_versions.wraps('3.13')
@utils.arg('group',
           metavar='<group>',
           help='Name or ID of a group.')
def do_group_show(cs, args):
    """Shows details of a group."""
    info = dict()
    group = shell_utils.find_group(cs, args.group)
    info.update(group._info)

    info.pop('links', None)
    utils.print_dict(info)


@api_versions.wraps('3.13')
@utils.arg('grouptype',
           metavar='<group-type>',
           help='Group type.')
@utils.arg('volumetypes',
           metavar='<volume-types>',
           help='Comma-separated list of volume types.')
@utils.arg('--name',
           metavar='<name>',
           help='Name of a group.')
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Description of a group. Default=None.')
@utils.arg('--availability-zone',
           metavar='<availability-zone>',
           default=None,
           help='Availability zone for group. Default=None.')
def do_group_create(cs, args):
    """Creates a group."""

    group = cs.groups.create(
        args.grouptype,
        args.volumetypes,
        args.name,
        args.description,
        availability_zone=args.availability_zone)

    info = dict()
    group = cs.groups.get(group.id)
    info.update(group._info)

    info.pop('links', None)
    utils.print_dict(info)


@api_versions.wraps('3.14')
@utils.arg('--group-snapshot',
           metavar='<group-snapshot>',
           help='Name or ID of a group snapshot. Default=None.')
@utils.arg('--source-group',
           metavar='<source-group>',
           help='Name or ID of a source group. Default=None.')
@utils.arg('--name',
           metavar='<name>',
           help='Name of a group. Default=None.')
@utils.arg('--description',
           metavar='<description>',
           help='Description of a group. Default=None.')
def do_group_create_from_src(cs, args):
    """Creates a group from a group snapshot or a source group."""
    if not args.group_snapshot and not args.source_group:
        msg = ('Cannot create group because neither '
               'group snapshot nor source group is provided.')
        raise exceptions.ClientException(code=1, message=msg)
    if args.group_snapshot and args.source_group:
        msg = ('Cannot create group because both '
               'group snapshot and source group are provided.')
        raise exceptions.ClientException(code=1, message=msg)
    group_snapshot = None
    if args.group_snapshot:
        group_snapshot = shell_utils.find_group_snapshot(cs,
                                                         args.group_snapshot)
    source_group = None
    if args.source_group:
        source_group = shell_utils.find_group(cs, args.source_group)
    info = cs.groups.create_from_src(
        group_snapshot.id if group_snapshot else None,
        source_group.id if source_group else None,
        args.name,
        args.description)

    info.pop('links', None)
    utils.print_dict(info)


@api_versions.wraps('3.13')
@utils.arg('group',
           metavar='<group>', nargs='+',
           help='Name or ID of one or more groups '
                'to be deleted.')
@utils.arg('--delete-volumes',
           action='store_true',
           default=False,
           help='Allows or disallows groups to be deleted '
                'if they are not empty. If the group is empty, '
                'it can be deleted without the delete-volumes flag. '
                'If the group is not empty, the delete-volumes '
                'flag is required for it to be deleted. If True, '
                'all volumes in the group will also be deleted.')
def do_group_delete(cs, args):
    """Removes one or more groups."""
    failure_count = 0
    for group in args.group:
        try:
            shell_utils.find_group(cs, group).delete(args.delete_volumes)
        except Exception as e:
            failure_count += 1
            print("Delete for group %s failed: %s" %
                  (group, e))
    if failure_count == len(args.group):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "groups.")


@api_versions.wraps('3.13')
@utils.arg('group',
           metavar='<group>',
           help='Name or ID of a group.')
@utils.arg('--name', metavar='<name>',
           help='New name for group. Default=None.')
@utils.arg('--description', metavar='<description>',
           help='New description for group. Default=None.')
@utils.arg('--add-volumes',
           metavar='<uuid1,uuid2,......>',
           help='UUID of one or more volumes '
                'to be added to the group, '
                'separated by commas. Default=None.')
@utils.arg('--remove-volumes',
           metavar='<uuid3,uuid4,......>',
           help='UUID of one or more volumes '
                'to be removed from the group, '
                'separated by commas. Default=None.')
def do_group_update(cs, args):
    """Updates a group."""
    kwargs = {}

    if args.name is not None:
        kwargs['name'] = args.name

    if args.description is not None:
        kwargs['description'] = args.description

    if args.add_volumes is not None:
        kwargs['add_volumes'] = args.add_volumes

    if args.remove_volumes is not None:
        kwargs['remove_volumes'] = args.remove_volumes

    if not kwargs:
        msg = ('At least one of the following args must be supplied: '
               'name, description, add-volumes, remove-volumes.')
        raise exceptions.ClientException(code=1, message=msg)

    shell_utils.find_group(cs, args.group).update(**kwargs)


@api_versions.wraps('3.14')
@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help="Filters results by a status. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--group-id',
           metavar='<group_id>',
           default=None,
           help="Filters results by a group ID. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_group_snapshot_list(cs, args):
    """Lists all group snapshots."""

    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    search_opts = {
        'all_tenants': all_tenants,
        'status': args.status,
        'group_id': args.group_id,
    }
    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))

    group_snapshots = cs.group_snapshots.list(search_opts=search_opts)

    columns = ['ID', 'Status', 'Name']
    utils.print_list(group_snapshots, columns)


@api_versions.wraps('3.14')
@utils.arg('group_snapshot',
           metavar='<group_snapshot>',
           help='Name or ID of group snapshot.')
def do_group_snapshot_show(cs, args):
    """Shows group snapshot details."""
    info = dict()
    group_snapshot = shell_utils.find_group_snapshot(cs, args.group_snapshot)
    info.update(group_snapshot._info)

    info.pop('links', None)
    utils.print_dict(info)


@api_versions.wraps('3.14')
@utils.arg('group',
           metavar='<group>',
           help='Name or ID of a group.')
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help='Group snapshot name. Default=None.')
@utils.arg('--description',
           metavar='<description>',
           default=None,
           help='Group snapshot description. Default=None.')
def do_group_snapshot_create(cs, args):
    """Creates a group snapshot."""
    group = shell_utils.find_group(cs, args.group)
    group_snapshot = cs.group_snapshots.create(
        group.id,
        args.name,
        args.description)

    info = dict()
    group_snapshot = cs.group_snapshots.get(group_snapshot.id)
    info.update(group_snapshot._info)

    info.pop('links', None)
    utils.print_dict(info)


@api_versions.wraps('3.14')
@utils.arg('group_snapshot',
           metavar='<group_snapshot>', nargs='+',
           help='Name or ID of one or more group snapshots to be deleted.')
def do_group_snapshot_delete(cs, args):
    """Removes one or more group snapshots."""
    failure_count = 0
    for group_snapshot in args.group_snapshot:
        try:
            shell_utils.find_group_snapshot(cs, group_snapshot).delete()
        except Exception as e:
            failure_count += 1
            print("Delete for group snapshot %s failed: %s" %
                  (group_snapshot, e))
    if failure_count == len(args.group_snapshot):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "group snapshots.")


@api_versions.wraps('3.0')
@utils.arg('--host', metavar='<hostname>', default=None,
           help='Host name. Default=None.')
@utils.arg('--binary', metavar='<binary>', default=None,
           help='Service binary. Default=None.')
@utils.arg('--withreplication',
           metavar='<True|False>',
           const=True,
           nargs='?',
           default=False,
           start_version='3.7',
           help='Enables or disables display of '
                'Replication info for c-vol services. Default=False.')
def do_service_list(cs, args):
    """Lists all services. Filter by host and service binary."""
    if hasattr(args, 'withreplication'):
        replication = strutils.bool_from_string(args.withreplication,
                                                strict=True)
    else:
        replication = False

    result = cs.services.list(host=args.host, binary=args.binary)
    columns = ["Binary", "Host", "Zone", "Status", "State", "Updated_at"]
    if cs.api_version.matches('3.7'):
        columns.append('Cluster')
    if replication:
        columns.extend(["Replication Status", "Active Backend ID", "Frozen"])
    # NOTE(jay-lau-513): we check if the response has disabled_reason
    # so as not to add the column when the extended ext is not enabled.
    if result and hasattr(result[0], 'disabled_reason'):
        columns.append("Disabled Reason")
    utils.print_list(result, columns)


@api_versions.wraps('3.8')
@utils.arg('host',
           metavar='<host>',
           help='Cinder host on which to list manageable snapshots; '
                'takes the form: host@backend-name#pool')
@utils.arg('--detailed',
           metavar='<detailed>',
           default=True,
           help='Returned detailed information (default true).')
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning volumes that appear later in the volume '
                'list than that represented by this reference. This reference '
                'should be json like. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of volumes to return. Default=None.')
@utils.arg('--offset',
           metavar='<offset>',
           default=None,
           help='Number of volumes to skip after marker. Default=None.')
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.'
                  ) % ', '.join(base.SORT_MANAGEABLE_KEY_VALUES)))
def do_snapshot_manageable_list(cs, args):
    """Lists all manageable snapshots."""
    # pylint: disable=function-redefined
    detailed = strutils.bool_from_string(args.detailed)
    snapshots = cs.volume_snapshots.list_manageable(host=args.host,
                                                    detailed=detailed,
                                                    marker=args.marker,
                                                    limit=args.limit,
                                                    offset=args.offset,
                                                    sort=args.sort)
    columns = ['reference', 'size', 'safe_to_manage', 'source_reference']
    if detailed:
        columns.extend(['reason_not_safe', 'cinder_id', 'extra_info'])
    utils.print_list(snapshots, columns, sortby_index=None)


@api_versions.wraps("3.0")
def do_api_version(cs, args):
    """Display the server API version information."""
    columns = ['ID', 'Status', 'Version', 'Min_version']
    response = cs.services.server_api_version()
    utils.print_list(response, columns)


@api_versions.wraps("3.3")
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           start_version='3.5',
           help='Begin returning message that appear later in the message '
                'list than that represented by this id. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           start_version='3.5',
           help='Maximum number of messages to return. Default=None.')
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           start_version='3.5',
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.') % ', '.join(base.SORT_KEY_VALUES)))
@utils.arg('--resource_uuid',
           metavar='<resource_uuid>',
           default=None,
           help="Filters results by a resource uuid. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--resource_type',
           metavar='<type>',
           default=None,
           help="Filters results by a resource type. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--event_id',
           metavar='<id>',
           default=None,
           help="Filters results by event id. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--request_id',
           metavar='<request_id>',
           default=None,
           help="Filters results by request id. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--level',
           metavar='<level>',
           default=None,
           help="Filters results by the message level. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_message_list(cs, args):
    """Lists all messages."""
    search_opts = {
        'resource_uuid': args.resource_uuid,
        'event_id': args.event_id,
        'request_id': args.request_id,
    }
    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))
    if args.resource_type:
        search_opts['resource_type'] = args.resource_type.upper()
    if args.level:
        search_opts['message_level'] = args.level.upper()

    marker = args.marker if hasattr(args, 'marker') else None
    limit = args.limit if hasattr(args, 'limit') else None
    sort = args.sort if hasattr(args, 'sort') else None

    messages = cs.messages.list(search_opts=search_opts,
                                marker=marker,
                                limit=limit,
                                sort=sort)

    columns = ['ID', 'Resource Type', 'Resource UUID', 'Event ID',
               'User Message']
    if sort:
        sortby_index = None
    else:
        sortby_index = 0
    utils.print_list(messages, columns, sortby_index=sortby_index)


@api_versions.wraps("3.3")
@utils.arg('message',
           metavar='<message>',
           help='ID of message.')
def do_message_show(cs, args):
    """Shows message details."""
    info = dict()
    message = shell_utils.find_message(cs, args.message)
    info.update(message._info)
    info.pop('links', None)
    utils.print_dict(info)


@api_versions.wraps("3.3")
@utils.arg('message',
           metavar='<message>', nargs='+',
           help='ID of one or more message to be deleted.')
def do_message_delete(cs, args):
    """Removes one or more messages."""
    failure_count = 0
    for message in args.message:
        try:
            shell_utils.find_message(cs, message).delete()
        except Exception as e:
            failure_count += 1
            print("Delete for message %s failed: %s" % (message, e))
    if failure_count == len(args.message):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "messages.")


@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=0,
           help='Shows details for all tenants. Admin only.')
@utils.arg('--all_tenants',
           nargs='?',
           type=int,
           const=1,
           help=argparse.SUPPRESS)
@utils.arg('--name',
           metavar='<name>',
           default=None,
           help="Filters results by a name. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--display-name',
           help=argparse.SUPPRESS)
@utils.arg('--display_name',
           help=argparse.SUPPRESS)
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help="Filters results by a status. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--volume-id',
           metavar='<volume-id>',
           default=None,
           help="Filters results by a volume ID. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--volume_id',
           help=argparse.SUPPRESS)
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning snapshots that appear later in the snapshot '
                'list than that represented by this id. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of snapshots to return. Default=None.')
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.') % ', '.join(base.SORT_KEY_VALUES)))
@utils.arg('--tenant',
           type=str,
           dest='tenant',
           nargs='?',
           metavar='<tenant>',
           help='Display information from single tenant (Admin only).')
@utils.arg('--metadata',
           nargs='*',
           metavar='<key=value>',
           default=None,
           start_version='3.22',
           help="Filters results by a metadata key and value pair. Require "
                "volume api version >=3.22. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_snapshot_list(cs, args):
    """Lists all snapshots."""
    # pylint: disable=function-redefined
    all_tenants = (1 if args.tenant else
                   int(os.environ.get("ALL_TENANTS", args.all_tenants)))

    if args.display_name is not None:
        args.name = args.display_name

    metadata = None
    try:
        if args.metadata:
            metadata = shell_utils.extract_metadata(args)
    except AttributeError:
        pass

    search_opts = {
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
        'volume_id': args.volume_id,
        'project_id': args.tenant,
        'metadata': metadata
    }

    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))

    snapshots = cs.volume_snapshots.list(search_opts=search_opts,
                                         marker=args.marker,
                                         limit=args.limit,
                                         sort=args.sort)
    shell_utils.translate_volume_snapshot_keys(snapshots)
    sortby_index = None if args.sort else 0
    utils.print_list(snapshots,
                     ['ID', 'Volume ID', 'Status', 'Name', 'Size'],
                     sortby_index=sortby_index)


@api_versions.wraps('3.27')
@utils.arg('--all-tenants',
           dest='all_tenants',
           metavar='<0|1>',
           nargs='?',
           type=int,
           const=1,
           default=utils.env('ALL_TENANTS', default=0),
           help='Shows details for all tenants. Admin only.')
@utils.arg('--volume-id',
           metavar='<volume-id>',
           default=None,
           help="Filters results by a volume ID. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--status',
           metavar='<status>',
           default=None,
           help="Filters results by a status. Default=None. "
                "%s" % FILTER_DEPRECATED)
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='Begin returning attachments that appear later in '
                'attachment list than that represented by this id. '
                'Default=None.')
@utils.arg('--limit',
           metavar='<limit>',
           default=None,
           help='Maximum number of attachments to return. Default=None.')
@utils.arg('--sort',
           metavar='<key>[:<direction>]',
           default=None,
           help=(('Comma-separated list of sort keys and directions in the '
                  'form of <key>[:<asc|desc>]. '
                  'Valid keys: %s. '
                  'Default=None.') % ', '.join(base.SORT_KEY_VALUES)))
@utils.arg('--tenant',
           type=str,
           dest='tenant',
           nargs='?',
           metavar='<tenant>',
           help='Display information from single tenant (Admin only).')
@utils.arg('--filters',
           type=str,
           nargs='*',
           start_version='3.33',
           metavar='<key=value>',
           default=None,
           help="Filter key and value pairs. Please use 'cinder list-filters' "
                "to check enabled filters from server, Default=None.")
def do_attachment_list(cs, args):
    """Lists all attachments."""
    search_opts = {
        'all_tenants': 1 if args.tenant else args.all_tenants,
        'project_id': args.tenant,
        'status': args.status,
        'volume_id': args.volume_id,
    }
    # Update search option with `filters`
    if hasattr(args, 'filters') and args.filters is not None:
        search_opts.update(shell_utils.extract_filters(args.filters))

    attachments = cs.attachments.list(search_opts=search_opts,
                                      marker=args.marker,
                                      limit=args.limit,
                                      sort=args.sort)
    columns = ['ID', 'Volume ID', 'Status', 'Server ID']
    if args.sort:
        sortby_index = None
    else:
        sortby_index = 0
    utils.print_list(attachments, columns, sortby_index=sortby_index)


@api_versions.wraps('3.27')
@utils.arg('attachment',
           metavar='<attachment>',
           help='ID of attachment.')
def do_attachment_show(cs, args):
    """Show detailed information for attachment."""
    attachment = cs.attachments.show(args.attachment)
    attachment_dict = attachment.to_dict()
    connection_dict = attachment_dict.pop('connection_info', {})
    utils.print_dict(attachment_dict)

    # TODO(jdg): Need to add checks here like admin/policy for displaying the
    # connection_info, this is still experimental so we'll leave it enabled for
    # now
    if connection_dict:
        utils.print_dict(connection_dict)


@api_versions.wraps('3.27')
@utils.arg('volume',
           metavar='<volume>',
           help='Name or ID of volume or volumes to attach.')
@utils.arg('server_id',
           metavar='<server_id>',
           help='ID of server attaching to.')
@utils.arg('--connect',
           metavar='<connect>',
           default=False,
           help='Make an active connection using provided connector info '
                '(True or False).')
@utils.arg('--initiator',
           metavar='<initiator>',
           default=None,
           help='iqn of the initiator attaching to.  Default=None.')
@utils.arg('--ip',
           metavar='<ip>',
           default=None,
           help='ip of the system attaching to.  Default=None.')
@utils.arg('--host',
           metavar='<host>',
           default=None,
           help='Name of the host attaching to. Default=None.')
@utils.arg('--platform',
           metavar='<platform>',
           default='x86_64',
           help='Platform type. Default=x86_64.')
@utils.arg('--ostype',
           metavar='<ostype>',
           default='linux2',
           help='OS type. Default=linux2.')
@utils.arg('--multipath',
           metavar='<multipath>',
           default=False,
           help='Use multipath. Default=False.')
@utils.arg('--mountpoint',
           metavar='<mountpoint>',
           default=None,
           help='Mountpoint volume will be attached at. Default=None.')
def do_attachment_create(cs, args):
    """Create an attachment for a cinder volume."""

    connector = {}
    if strutils.bool_from_string(args.connect, strict=True):
        # FIXME(jdg): Add in all the options when they're finalized
        connector = {'initiator': args.initiator,
                     'ip': args.ip,
                     'platform': args.platform,
                     'host': args.host,
                     'os_type': args.ostype,
                     'multipath': args.multipath,
                     'mountpoint': args.mountpoint}
    attachment = cs.attachments.create(args.volume,
                                       connector,
                                       args.server_id)
    connector_dict = attachment.pop('connection_info', None)
    utils.print_dict(attachment)
    if connector_dict:
        utils.print_dict(connector_dict)


@api_versions.wraps('3.27')
@utils.arg('attachment',
           metavar='<attachment>',
           help='ID of attachment.')
@utils.arg('--initiator',
           metavar='<initiator>',
           default=None,
           help='iqn of the initiator attaching to.  Default=None.')
@utils.arg('--ip',
           metavar='<ip>',
           default=None,
           help='ip of the system attaching to.  Default=None.')
@utils.arg('--host',
           metavar='<host>',
           default=None,
           help='Name of the host attaching to. Default=None.')
@utils.arg('--platform',
           metavar='<platform>',
           default='x86_64',
           help='Platform type. Default=x86_64.')
@utils.arg('--ostype',
           metavar='<ostype>',
           default='linux2',
           help='OS type. Default=linux2.')
@utils.arg('--multipath',
           metavar='<multipath>',
           default=False,
           help='Use multipath. Default=False.')
@utils.arg('--mountpoint',
           metavar='<mountpoint>',
           default=None,
           help='Mountpoint volume will be attached at. Default=None.')
def do_attachment_update(cs, args):
    """Update an attachment for a cinder volume.
    This call is designed to be more of an attachment completion than anything
    else.  It expects the value of a connector object to notify the driver that
    the volume is going to be connected and where it's being connected to.
    """
    connector = {'initiator': args.initiator,
                 'ip': args.ip,
                 'platform': args.platform,
                 'host': args.host,
                 'os_type': args.ostype,
                 'multipath': args.multipath,
                 'mountpoint': args.mountpoint}
    attachment = cs.attachments.update(args.attachment,
                                       connector)
    attachment_dict = attachment.to_dict()
    connector_dict = attachment_dict.pop('connection_info', None)
    utils.print_dict(attachment_dict)
    if connector_dict:
        utils.print_dict(connector_dict)


@api_versions.wraps('3.27')
@utils.arg('attachment',
           metavar='<attachment>', nargs='+',
           help='ID of attachment or attachments to delete.')
def do_attachment_delete(cs, args):
    """Delete an attachment for a cinder volume."""
    for attachment in args.attachment:
        cs.attachments.delete(attachment)


@api_versions.wraps('3.0')
def do_version_list(cs, args):
    """List all API versions."""
    result = cs.services.server_api_version()
    if 'min_version' in dir(result[0]):
        columns = ["Id", "Status", "Updated", "Min Version", "Version"]
    else:
        columns = ["Id", "Status", "Updated"]

    print("Client supported API versions:")
    print("Minimum version %(v)s" %
          {'v': api_versions.MIN_VERSION})
    print("Maximum version %(v)s" %
          {'v': api_versions.MAX_VERSION})

    print("\nServer supported API versions:")
    utils.print_list(result, columns)
