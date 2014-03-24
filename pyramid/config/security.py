from pyramid.interfaces import (
    IAuthorizationPolicy,
    IAuthenticationPolicy,
    IDefaultPermission,
    PHASE1_CONFIG,
    PHASE2_CONFIG,
    )

from pyramid.exceptions import ConfigurationError
from pyramid.util import action_method

class SecurityConfiguratorMixin(object):
    @action_method
    def set_authentication_policy(self, policy):
        """ Override the :app:`Pyramid` :term:`authentication policy` in the
        current configuration.  The ``policy`` argument must be an instance
        of an authentication policy or a :term:`dotted Python name`
        that points at an instance of an authentication policy.

        .. note::

           Using the ``authentication_policy`` argument to the
           :class:`pyramid.config.Configurator` constructor can be used to
           achieve the same purpose.

        """
        def register():
            self._set_authentication_policy(policy)
            if self.registry.queryUtility(IAuthorizationPolicy) is None:
                raise ConfigurationError(
                    'Cannot configure an authentication policy without '
                    'also configuring an authorization policy '
                    '(use the set_authorization_policy method)')
        intr = self.introspectable('authentication policy', None,
                                   self.object_description(policy),
                                   'authentication policy')
        intr['policy'] = policy
        # authentication policy used by view config (phase 3)
        self.action(IAuthenticationPolicy, register, order=PHASE2_CONFIG,
                    introspectables=(intr,))

    def _set_authentication_policy(self, policy):
        policy = self.maybe_dotted(policy)
        self.registry.registerUtility(policy, IAuthenticationPolicy)

    @action_method
    def set_authorization_policy(self, policy):
        """ Override the :app:`Pyramid` :term:`authorization policy` in the
        current configuration.  The ``policy`` argument must be an instance
        of an authorization policy or a :term:`dotted Python name` that points
        at an instance of an authorization policy.

        .. note::

           Using the ``authorization_policy`` argument to the
           :class:`pyramid.config.Configurator` constructor can be used to
           achieve the same purpose.
        """
        def register():
            self._set_authorization_policy(policy)
        def ensure():
            if self.autocommit:
                return
            if self.registry.queryUtility(IAuthenticationPolicy) is None:
                raise ConfigurationError(
                    'Cannot configure an authorization policy without '
                    'also configuring an authentication policy '
                    '(use the set_authorization_policy method)')

        intr = self.introspectable('authorization policy', None,
                                   self.object_description(policy),
                                   'authorization policy')
        intr['policy'] = policy
        # authorization policy used by view config (phase 3) and
        # authentication policy (phase 2)
        self.action(IAuthorizationPolicy, register, order=PHASE1_CONFIG,
                    introspectables=(intr,))
        self.action(None, ensure)

    def _set_authorization_policy(self, policy):
        policy = self.maybe_dotted(policy)
        self.registry.registerUtility(policy, IAuthorizationPolicy)

    @action_method
    def set_default_permission(self, permission):
        """
        Set the default permission to be used by all subsequent
        :term:`view configuration` registrations.  ``permission``
        should be a :term:`permission` string to be used as the
        default permission.  An example of a permission
        string:``'view'``.  Adding a default permission makes it
        unnecessary to protect each view configuration with an
        explicit permission, unless your application policy requires
        some exception for a particular view.

        If a default permission is *not* set, views represented by
        view configuration registrations which do not explicitly
        declare a permission will be executable by entirely anonymous
        users (any authorization policy is ignored).

        Later calls to this method override will conflict with earlier calls;
        there can be only one default permission active at a time within an
        application.

        .. warning::

          If a default permission is in effect, view configurations meant to
          create a truly anonymously accessible view (even :term:`exception
          view` views) *must* use the value of the permission importable as
          :data:`pyramid.security.NO_PERMISSION_REQUIRED`.  When this string
          is used as the ``permission`` for a view configuration, the default
          permission is ignored, and the view is registered, making it
          available to all callers regardless of their credentials.

        .. seealso::

            See also :ref:`setting_a_default_permission`.

        .. note::

           Using the ``default_permission`` argument to the
           :class:`pyramid.config.Configurator` constructor can be used to
           achieve the same purpose.
        """
        def register():
            self.registry.registerUtility(permission, IDefaultPermission)
        intr = self.introspectable('default permission',
                                   None,
                                   permission,
                                   'default permission')
        intr['value'] = permission
        perm_intr = self.introspectable('permissions',
                                        permission,
                                        permission,
                                        'permission')
        perm_intr['value'] = permission
        # default permission used during view registration (phase 3)
        self.action(IDefaultPermission, register, order=PHASE1_CONFIG,
                    introspectables=(intr, perm_intr,))


    def add_permission(self, permission_name):
        """
        A configurator directive which registers a free-standing
        permission without associating it with a view callable.  This can be
        used so that the permission shows up in the introspectable data under
        the ``permissions`` category (permissions mentioned via ``add_view``
        already end up in there).  For example::

          config = Configurator()
          config.add_permission('view')
        """
        intr = self.introspectable(
            'permissions',
            permission_name,
            permission_name,
            'permission'
            )
        intr['value'] = permission_name
        self.action(None, introspectables=(intr,))

