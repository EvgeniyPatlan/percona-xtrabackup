%define xb_version_major  @@XB_VERSION_MAJOR@@
%define xb_version_minor  @@XB_VERSION_MINOR@@
%define xb_version_patch  @@XB_VERSION_PATCH@@
%define xb_version_extra  @@XB_VERSION_EXTRA@@
%define xb_rpm_version_extra @@XB_RPM_VERSION_EXTRA@@
%define xb_revision       @@XB_REVISION@@
%define rpm_release       @@RPM_RELEASE@@

%global mysqldatadir /var/lib/mysql

# Common cmake flags shared between release and debug builds
%global cmake_common_flags \
  -DBUILD_CONFIG=xtrabackup_release \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DWITH_SSL=system \
  -DINSTALL_MANDIR=%{_mandir} \
  -DWITH_MAN_PAGES=1 \
  -DMINIMAL_RELWITHDEBINFO=OFF \
  -DINSTALL_MYSQLTESTDIR=%{_datadir}/percona-xtrabackup-test-%{xb_version_major}%{xb_version_minor} \
  -DDOWNLOAD_BOOST=1 \
  -DWITH_BOOST=libboost \
  -DMYSQL_UNIX_ADDR="%{mysqldatadir}/mysql.sock" \
  -DINSTALL_PLUGINDIR="%{_lib}/xtrabackup/plugin" \
  -DFORCE_INSOURCE_BUILD=1 \
  -DWITH_ZLIB=bundled \
  -DWITH_ZSTD=bundled \
  -DWITH_PROTOBUF=bundled

#####################################
Name:           percona-xtrabackup-%{xb_version_major}%{xb_version_minor}
Version:        %{xb_version_major}.%{xb_version_minor}.%{xb_version_patch}
Release:        %{xb_rpm_version_extra}%{?dist}
Summary:        XtraBackup online backup for MySQL / InnoDB

Group:          Applications/Databases
License:        GPLv2
URL:            http://www.percona.com/software/percona-xtrabackup
Source:         percona-xtrabackup-%{version}%{xb_version_extra}.tar.gz
Source999:      call-home.sh

BuildRequires:  cmake, libaio-devel, libgcrypt-devel, ncurses-devel, readline-devel
BuildRequires:  zlib-devel, libev-devel, openssl-devel, libcurl-devel
Conflicts:      percona-xtrabackup-21, percona-xtrabackup-22, percona-xtrabackup, percona-xtrabackup-24
Requires:       perl(DBD::mysql), rsync, zstd
Requires:       perl(Digest::MD5), lz4


%description
Percona XtraBackup is OpenSource online (non-blockable) backup solution for InnoDB and XtraDB engines

%package -n percona-xtrabackup-test-%{xb_version_major}%{xb_version_minor}
Summary:        Test suite for Percona XtraBackup
Group:          Applications/Databases
Requires:       percona-xtrabackup-%{xb_version_major}%{xb_version_minor} = %{version}-%{release}
Requires:       /usr/bin/mysql
AutoReqProv:    no

%description -n percona-xtrabackup-test-%{xb_version_major}%{xb_version_minor}
This package contains the test suite for Percona XtraBackup %{version}%{xb_version_extra}

%prep
%setup -q -n percona-xtrabackup-%{version}%{xb_version_extra}

%bcond_with dummy

%build
%if %{with dummy}
echo 'int main() { return 300; }' | gcc -x c - -o storage/innobase/xtrabackup/src/xtrabackup
echo 'int main() { return 300; }' | gcc -x c - -o storage/innobase/xtrabackup/src/xbstream
echo 'int main() { return 300; }' | gcc -x c - -o storage/innobase/xtrabackup/src/xbcrypt
echo 'int main() { return 300; }' | gcc -x c - -o storage/innobase/xtrabackup/src/xbcloud
%else

export CC=${CC-"gcc"}
export CXX=${CXX-"g++"}
export CFLAGS=${CFLAGS:-}
export CXXFLAGS=${CXXFLAGS:-}

# Debug build
mkdir debug
cd debug
cmake .. %{cmake_common_flags} -DCMAKE_BUILD_TYPE=Debug
make %{?_smp_mflags}
cd ..

# Release build
cmake . %{cmake_common_flags}
make %{?_smp_mflags}

%endif

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

cp -v debug/bin/xtrabackup $RPM_BUILD_ROOT/%{_bindir}/xtrabackup-debug
patchelf --set-rpath '$ORIGIN/../lib/private' $RPM_BUILD_ROOT/%{_bindir}/xtrabackup-debug

rm -rf $RPM_BUILD_ROOT/%{_libdir}/libmysqlservices.a
rm -rf $RPM_BUILD_ROOT/usr/lib/libmysqlservices.a
rm -rf $RPM_BUILD_ROOT/usr/docs/INFO_SRC
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man8
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man1/c*
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man1/m*
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man1/i*
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man1/l*
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man1/p*
rm -rf $RPM_BUILD_ROOT/%{_mandir}/man1/z*

%post
cp %SOURCE999 /tmp/ 2>/dev/null ||
bash /tmp/call-home.sh -f "PRODUCT_FAMILY_PXB" -v %{xb_version_major}.%{xb_version_minor}.%{xb_version_patch}%{xb_version_extra}-%{rpm_release} -d "PACKAGE" &>/dev/null || :
rm -f /tmp/call-home.sh

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/xtrabackup
%{_bindir}/xtrabackup-debug
%{_bindir}/xbstream
%{_bindir}/xbcrypt
%{_bindir}/xbcloud
%{_bindir}/xbcloud_osenv
/usr/lib/private/libprotobuf*
/usr/lib/private/icudt73l
%{_libdir}/xtrabackup/plugin/keyring_file.so
%{_libdir}/xtrabackup/plugin/keyring_vault.so
%{_libdir}/xtrabackup/plugin/component_keyring_file.so
%{_libdir}/xtrabackup/plugin/component_keyring_kms.so
%{_includedir}/kmip.h
%{_includedir}/kmippp.h
/usr/lib/libkmip.a
/usr/lib/libkmippp.a
%{_libdir}/xtrabackup/plugin/component_keyring_kmip.so
%doc LICENSE
%doc %{_mandir}/man1/*.1.gz

%files -n percona-xtrabackup-test-%{xb_version_major}%{xb_version_minor}
%defattr(-,root,root,-)
%{_datadir}/percona-xtrabackup-test-%{xb_version_major}%{xb_version_minor}

%changelog
* Fri Aug 31 2018 Evgeniy Patlan <evgeniy.patlan@percona.com>
- Packaging for 8.0
