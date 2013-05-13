Name:           openlmi-storage
Version:        v0.5.1.pre2_1_gbefad31
Release:        1
Summary:        CIM providers for storage management

License:        LGPLv2+
URL:            http://fedorahosted.org/openlmi
Source0:        https://fedorahosted.org/released/openlmi-storage/%{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python2-devel
Requires:       cmpi-bindings-pywbem
Requires:       python-blivet
Requires:       openlmi-python
# For Linux_ComputerSystem:
Requires:       sblim-cmpi-base
# For openlmi-mof-register script:
Requires(pre):  openlmi-providers >= 0.0.17
Requires(preun): openlmi-providers >= 0.0.17
Requires(post): openlmi-providers >= 0.0.17
# For LMI_LogicalFile:
Requires:       openlmi-logicalfile

%description
The openlmi-storage package contains CMPI providers for management of storage
using Common Information Managemen (CIM) protocol.

The providers can be registered in any CMPI-aware CIMOM, both OpenPegasus and
SFCB were tested.

%prep
%setup

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}
install -m 644 mof/* $RPM_BUILD_ROOT/%{_datadir}/%{name}/

%pre
# If upgrading, deregister old version
if [ "$1" -gt 1 ]; then
    openlmi-mof-register unregister \
        %{_datadir}/%{name}/*.mof \
        %{_datadir}/%{name}/LMI_Storage.reg \
        > /dev/null 2>&1 || :
fi

%post
# Register Schema and Provider
if [ "$1" -ge 1 ]; then
    %{_bindir}/openlmi-mof-register register \
        %{_datadir}/%{name}/6*_LMI_Storage.mof \
        %{_datadir}/%{name}/LMI_Storage.reg \
        > /dev/null 2>&1 || :
fi

%preun
# Deregister only if not upgrading
if [ "$1" -eq 0 ]; then
    %{_bindir}/openlmi-mof-register unregister \
        %{_datadir}/%{name}/6*_LMI_Storage.mof \
        %{_datadir}/%{name}/LMI_Storage.reg \
        > /dev/null 2>&1 || :
fi


%files
%doc README COPYING CHANGES
%{python_sitelib}/*
%{_datadir}/%{name}

%changelog
* Mon May 13 2013 Jan Safranek <jsafrane@redhat.com> - 0.5.1
- Create the spec file.
