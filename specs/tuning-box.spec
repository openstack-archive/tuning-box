%define name tuning-box
%{!?version: %define version 1.0.0}
%{!?release: %define release 1}

Name:           %{name}
Version:        %{version}
Release:        %{release}
Source0:        %{name}-%{version}.tar.gz
Summary:        Fuel ConfigDB extension package
URL:            http://openstack.org
License:        Apache
Group:          Development/Libraries
BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot
Prefix:         %{_prefix}
BuildRequires:  git
BuildRequires:  python-setuptools
BuildRequires:  python2-devel
BuildArch:      noarch

Requires:       fuel-nailgun
Requires:       python-alembic
Requires:       python-flask
Requires:       python-flask-sqlalchemy
Requires:       python-flask-restful

%description
This package provides extension to the Nailgun API. This extension allows to
manage deployment information and facilitates the exchange of such information
between Nailgun and 3rd-party deployment and configuration management services
(e.g. Puppet Master).

%prep
%setup -cq -n %{name}-%{version}

%build
cd %{_builddir}/%{name}-%{version} && python setup.py build

%install
cd %{_builddir}/%{name}-%{version} && %{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT
install -d -m 755 %{buildroot}%{_sysconfdir}/tuning-box

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/tuning-box/

%changelog
* Fri Mar 18 2016 Oleg Gelbukh <ogelbukh@mirantis.com> 9.0.0
- Initial version of package spec
