# Restore old style debuginfo creation for rpm >= 4.14.
%undefine _debugsource_packages
%undefine _debuginfo_subpackages

# -*- rpm-spec -*-
Summary:        RPM package
Name:           ubs-engine
ExclusiveArch:  aarch64
Version:        1.0.0
Release:        54
License:        Mulan PSL v2
URL:            https://atomgit.com/openeuler/ubs-engine
Source0:        %{name}-%{version}.tar.gz
Group:          System Environment/Base
Vendor:         Huawei Technologies Co., Ltd.
Prefix: /usr

BuildRequires:  cmake >= 3.22 make >= 4.3 gcc-c++ >= 10.3 gcc >= 10.3
BuildRequires:  glibc-devel >= 2.34 libstdc++-devel >= 10.3
BuildRequires:  systemd-devel >= 249
BuildRequires:  libboundscheck >= v1.1 libxml2-devel >= 2.9 openssl-devel >= 3.0 cpp-httplib-devel >= 0.27.0 rapidjson-devel >= 1.1.0 ubs-comm-devel >= 1.0.0-15
BuildRequires:  numactl-libs >= 2.0
BuildRequires:  ninja-build >= 1.10 bash bc coreutils sudo util-linux-user patch
BuildRequires:  libvirt-devel >= 9.0
Requires: glibc >= 2.34 libgcc >= 10.3 libstdc++ >= 10.3 libboundscheck >= v1.1 libxml2 >= 2.9 openssl-libs >= 3.0 cpp-httplib >= 0.27.0 ubs-comm-lib >= 1.0.0-15 libobmm
Requires: tar systemd
Requires(pre): coreutils shadow systemd glibc-common
Requires(post): coreutils gawk util-linux systemd grep sed
Requires(preun): systemd grep
Requires(postun): coreutils gawk util-linux systemd shadow glibc-common
%define _rpmdir %_topdir/RPMS
%define _srcrpmdir %_topdir/SRPMS
%define _unpackaged_files_terminate_build 0

%description
UBS Engine


# ========================================================
#                   SUBPACKAGE: ubs-engine-client-libs
# ========================================================
%define lib_name libubse-client
%define lib_soversion 1

%package client-libs
Summary: UBSE client shared library for third-party integration
Provides: %{lib_name}.so.%{lib_soversion}
Requires: libboundscheck, libstdc++
Obsoletes: %{name}-client-libs < %{version}-%{release}
Provides: %{name}-client-libs = %{version}-%{release}

%description client-libs
UBSE client shared library (%{lib_name}.so.%{lib_soversion}) for third-party applications to access UBSE services.
This package contains the runtime shared library required by programs that dynamically link to UBSE.


# ========================================================
#                   SUBPACKAGE: ubs-engine-client-devel
# ========================================================
%package client-devel
Summary: Development package for UBSE client SDK
Requires: %{name}-client-libs = %{version}-%{release}
Requires: pkgconfig
Provides: %{name}-client-devel = %{version}-%{release}

%description client-devel
Header files and static libraries for developing applications that use the UBSE client SDK.
This package is required for compiling programs that link against UBSE.


# ========================================================
#                   SUBPACKAGE: python3-ubs-engine
# ========================================================
%package -n python3-%{name}
Summary: Development package for UBSE python SDK
BuildArch: noarch
%description -n python3-%{name}
Development package for UBSE python SDK

# ========================================================
#                   SUBPACKAGE: ubs-engine-virtagent
# ========================================================
%package virtagent
Summary: virtagent plugin
Requires: %{name} = %{version}-%{release}
%description virtagent
Package for virt_agent plugin

# ========================================================
#                   SUBPACKAGE: ubs-engine-ucache
# ========================================================
%package ucache
Summary: ucache plugin
Requires: %{name} = %{version}-%{release}
%description ucache
Development package for ucache plugin

# ========================================================
#                   SUBPACKAGE: ubs-engine-rmrs
# ========================================================
%package rmrs
Summary: rmrs plugin
Requires: %{name} = %{version}-%{release}
Requires(post): coreutils shadow
%description rmrs
Development package for rmrs plugin
%post rmrs
if id "ubse" > /dev/null 2>&1; then
    usermod -aG ubturbo ubse
    usermod -aG libvirt ubse
    echo "Success: ubse user added to ubturbo and libvirt groups"
else
    echo "Warning: ubse user does not exist, skip group addition" >&2
fi

%define project_dir %{name}-%{version}
%define cmake_build_dir cmake-build-relwithdebinfo

%define log_dir /var/log/ubse
%define data_dir /var/lib/ubse
%define cert_dir /var/lib/ubse/cert
%define lcne_cert_dir /var/lib/ubse/lcne_cert
%define socket_dir /var/run/ubse

%define system_user ubse
%define system_group ubse
%define ubm_group ubm_nuds
%define service_name ubse.service

%define ensure_directory_owner() ensure_directory_owner() { \
    local dir_path="$1" \
    local recursive="${2:-false}" \
    if [ ! -d "$dir_path" ]; then \
        mkdir -p "$dir_path" \
    fi \
    local current_owner \
    current_owner=$(stat -c "%U:%G" "$dir_path") \
    if [ "$current_owner" != "%{system_user}:%{system_group}" ]; then \
        chown "%{system_user}:%{system_group}" "$dir_path" \
    fi \
    if [ "$recursive" = true ]; then \
        chown -R "%{system_user}:%{system_group}" "$dir_path" \
    fi \
}

%define deleted_semaphore() deleted_semaphore() { \
    echo "Checking and deleting semaphores..." \
    while read -r line; do \
        semid=$(echo "$line" | awk '{print $1}') \
        owner=$(echo "$line" | awk '{print $2}') \
        echo "Checking semaphore ID: $semid, Owner: $owner" \
        if [ "$owner" = "%{system_user}" ]; then \
            echo "Deleting semaphore $semid..." \
            if ! ipcrm -s $semid; then \
                echo "Failed to delete semaphore $semid" \
            else \
                echo "Deleted semaphore $semid" \
            fi \
        fi \
    done < <(ipcs -s | awk '/^[0-9]/ {print $2, $3, $4}') \
    echo "delete %{system_user} semaphores finished" \
}

%define update_config() update_config() { \
    config_file="$1" \
    if grep -q '^# mempooling=777' "$config_file"; then \
        sed -i 's/^# mempooling=777/mempooling=777/' "$config_file" \
    fi \
    if grep -q '^# virt_agent=205' "$config_file"; then \
        sed -i 's/^# virt_agent=205/virt_agent=205/' "$config_file" \
    fi \
    if ! grep -q 'mempooling=777' "$config_file"; then \
        echo "mempooling=777" >> "$config_file" \
    fi \
    if ! grep -q 'virt_agent=205' "$config_file"; then \
        echo "virt_agent=205" >> "$config_file" \
    fi \
}

%define remove_directory() remove_directory() { \
    if [ -d "$1" ]; then \
        rm -rf "$1" \
    fi \
}


%prep
%setup -q -T -b 0 -c -n %{project_dir}

%build
cd %{_builddir}/%{project_dir}/
bash build.sh -T RelWithDebInfo
%py3_build

%install
#install main package
mkdir -p %{buildroot}/usr/bin
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/bin/ubse %{buildroot}/usr/bin
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/bin/ubsectl %{buildroot}/usr/bin

mkdir -p %{buildroot}/usr/lib/systemd/system/
cp %{_builddir}/%{project_dir}/scripts/rpm/%{service_name} %{buildroot}/usr/lib/systemd/system/

mkdir -p %{buildroot}/etc/ubse/
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/conf/ubse*.conf %{buildroot}/etc/ubse/
mkdir -p %{buildroot}/etc/ubse/plugins

mkdir -p %{buildroot}/etc/bash_completion.d/
cp -f %{_builddir}/%{project_dir}/scripts/command_completion/cli_commands.sh %{buildroot}/etc/bash_completion.d/

mkdir -p %{buildroot}/usr/lib64

#install virtagent
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/lib/libvirtagent.so %{buildroot}/usr/lib64/
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/lib/libstrategy.so %{buildroot}/usr/lib64/
cp %{_builddir}/%{project_dir}/src/addons/virt_agent/conf/plugin_virt_agent.conf %{buildroot}/etc/ubse/plugins/
cp %{_builddir}/%{project_dir}/src/addons/virt_agent/conf/auth-virt_agent.conf %{buildroot}/etc/ubse/plugins/
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/lib/libubs-virt-agent.so.1.0.0 %{buildroot}/usr/lib64/
ln -sf libubs-virt-agent.so.1.0.0 %{buildroot}/usr/lib64/libubs-virt-agent.so.1
ln -sf libubs-virt-agent.so.1 %{buildroot}/usr/lib64/libubs-virt-agent.so
mkdir -p %{buildroot}/usr/include/virt_agent
cp -r %{_builddir}/%{project_dir}/src/addons/virt_agent/sdk/include/* %{buildroot}/usr/include/virt_agent/


#install client-libs
cmake --install %{_builddir}/%{project_dir}/%{cmake_build_dir} \
    --component ubse_sdk \
    --prefix %{buildroot}/usr
ln -sf libubse-client.so.1.0.0 %{buildroot}/usr/lib64/libubse-client.so.1

#install client-devel
ln -sf libubse-client.so.1 %{buildroot}/usr/lib64/libubse-client.so
chmod 644 %{buildroot}/usr/lib64/libubse-client.a
cp -r %{_builddir}/%{project_dir}/src/include/* %{buildroot}/usr/include/ubse

#install ucache
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/lib/libucache_plugin.so %{buildroot}/usr/lib64/
cp %{_builddir}/%{project_dir}/src/addons/ucache/conf/plugin_ucache.conf %{buildroot}/etc/ubse/plugins/

#install rmrs
cp %{_builddir}/%{project_dir}/%{cmake_build_dir}/lib/libmempooling.so %{buildroot}/usr/lib64/
cp %{_builddir}/%{project_dir}/src/addons/rmrs/conf/plugin_mempooling.conf %{buildroot}/etc/ubse/plugins/
mkdir -p %{buildroot}/usr/local/mempooling/include/mempooling/
cp %{_builddir}/%{project_dir}/src/addons/rmrs/interface/mempooling_interface.h %{buildroot}/usr/local/mempooling/include/mempooling/


#install python-sdk
%py3_install


%pre
set -e
print_error() {
    echo "ERROR" "$1"
    exit 1
}

create_user() {
    local requested_uid=""
    local requested_gid=""

    if [ -n "${UBSE_USER_UID:-}" ]; then
        if [[ "${UBSE_USER_UID}" =~ ^[0-9]+$ ]] && [ "$UBSE_USER_UID" -ge 0 ]; then
            requested_uid="$UBSE_USER_UID"
        else
            print_error "Invalid UBSE_USER_UID: '$UBSE_USER_UID'. Must be a non-negative integer."
        fi
    fi

    if [ -n "${UBSE_USER_GID:-}" ]; then
        if [[ "${UBSE_USER_GID}" =~ ^[0-9]+$ ]] && [ "$UBSE_USER_GID" -ge 0 ]; then
            requested_gid="$UBSE_USER_GID"
        else
            print_error "Invalid UBSE_USER_GID: '$UBSE_USER_GID'. Must be a non-negative integer."
        fi
    fi

    local user_exists=false
    local group_exists=false

    if getent passwd %{system_user} > /dev/null; then
        user_exists=true
    fi

    if getent group %{system_group} > /dev/null; then
        group_exists=true
    fi

    if $user_exists; then
        local current_uid=$(getent passwd %{system_user} | cut -d: -f3)
        local current_gid=$(getent passwd %{system_user} | cut -d: -f4)
        if [ -n "$requested_uid" ] && [ "$current_uid" != "$requested_uid" ]; then
            print_error "User %{system_user} exists with UID $current_uid, but requested UID is $requested_uid. Cannot change UID automatically."
        fi
        if [ -n "$requested_gid" ] && [ "$current_gid" != "$requested_gid" ]; then
            print_error "User %{system_user} exists with GID $current_gid, but requested GID is $requested_gid. Cannot change GID automatically."
        fi
    fi

    if $group_exists; then
        local current_gid=$(getent group %{system_group} | cut -d: -f3)
        if [ -n "$requested_gid" ] && [ "$current_gid" != "$requested_gid" ]; then
            print_error "Group %{system_group} exists with GID $current_gid, but requested GID is $requested_gid. Cannot change GID automatically."
        fi
    fi

    local group_args=("-r")
    if [ -n "$requested_gid" ]; then
        group_args+=(-g "$requested_gid")
    fi
    $group_exists || groupadd "${group_args[@]}" %{system_group} || print_error "Failed to create group %{system_group}"

    local user_args=("-r" "-g" "%{system_group}" "-s" "/sbin/nologin")
    if [ -n "$requested_uid" ]; then
        user_args+=("-u" "$requested_uid")
    fi
    $user_exists || useradd "${user_args[@]}" %{system_user} || print_error "Failed to create user %{system_user}"
}

if systemctl cat %{service_name} >/dev/null 2>&1 ; then
    systemctl stop %{service_name} || true
    systemctl disable %{service_name} || true
fi
create_user

if getent group %{ubm_group} > /dev/null; then
    usermod -aG %{ubm_group} %{system_user}
else
    echo "[WARN] Group '%{ubm_group}' not found. User '%{system_user}' was not added to this group. If UBM is required, please install the corresponding package and run: usermod -aG %{ubm_group} %{system_user}"
fi

%post
set -e
%{ensure_directory_owner}
%{deleted_semaphore}
%{update_config}
systemctl daemon-reload
ensure_directory_owner "%{log_dir}" true
ensure_directory_owner "%{data_dir}" true
ensure_directory_owner "%{data_dir}/data" true
ensure_directory_owner "%{cert_dir}" true
ensure_directory_owner "%{lcne_cert_dir}" true
ensure_directory_owner "%{socket_dir}" true
chmod 750 "%{log_dir}" "%{data_dir}" "%{data_dir}/data"
chmod 755 "%{socket_dir}"
chmod 700 "%{cert_dir}"
chmod 700 "%{lcne_cert_dir}"
systemctl enable %{service_name}
if [ "$MXE_SCENE" == "vm" ]; then
    update_config /etc/ubse/ubse_plugin_admission.conf
fi
deleted_semaphore


%preun
set -e
if [ "$1" -ne 0 ]; then
    exit 0
fi
if systemctl cat %{service_name} >/dev/null 2>&1 ; then
    systemctl stop %{service_name} || true
    systemctl disable %{service_name} || true
fi
if systemctl list-units --type=service | grep -q %{service_name}; then
    systemctl reset-failed %{service_name} || true
fi


%postun
if [ "$1" -ne 0 ]; then
    exit 0
fi
%{deleted_semaphore}
%{remove_directory}
systemctl daemon-reload
remove_directory %{log_dir}
remove_directory %{cert_dir}
remove_directory %{socket_dir}
remove_directory %{lcne_cert_dir}

deleted_semaphore
if id "%{system_user}" &>/dev/null; then
    userdel -r "%{system_user}" &>/dev/null || true
fi
if getent group "%{system_group}" &>/dev/null; then
    groupdel "%{system_group}"
fi

%files
%defattr(755,root,root,-)
/usr/bin/ubse
/usr/bin/ubsectl
%defattr(644,root,root,-)
/usr/lib/systemd/system/ubse.service
%defattr(644,root,root,755)
%dir /etc/ubse/
%config(noreplace) /etc/ubse/ubse*.conf
%dir /etc/ubse/plugins
%defattr(644,root,root,-)
/etc/bash_completion.d/cli_commands.sh

%files client-libs
%defattr(755,root,root,-)
/usr/lib64/libubse-client.so.1.0.0
%defattr(-,root,root,-)
/usr/lib64/libubse-client.so.1

%files client-devel
%defattr(-,root,root,-)
/usr/lib64/libubse-client.so
/usr/lib64/libubse-client.a
%defattr(644,root,root,755)
/usr/include/ubse/

%files -n python3-%{name}
%{python3_sitelib}/ubse/
%{python3_sitelib}/ubse-%{version}*.egg-info

%files virtagent
%defattr(644,root,root,-)
%config(noreplace) /etc/ubse/plugins/plugin_virt_agent.conf
%config(noreplace) /etc/ubse/plugins/auth-virt_agent.conf
%defattr(755,root,root,-)
/usr/lib64/libvirtagent.so
/usr/lib64/libstrategy.so
/usr/lib64/libubs-virt-agent.so.1.0.0
%defattr(-,root,root,-)
/usr/lib64/libubs-virt-agent.so.1
/usr/lib64/libubs-virt-agent.so
%defattr(644,root,root,755)
/usr/include/virt_agent/

%files ucache
%defattr(644,root,root,-)
%config(noreplace) /etc/ubse/plugins/plugin_ucache.conf
%defattr(755,root,root,-)
/usr/lib64/libucache_plugin.so

%files rmrs
%defattr(644,root,root,-)
%config(noreplace) /etc/ubse/plugins/plugin_mempooling.conf
%defattr(755,root,root,-)
/usr/lib64/libmempooling.so
%defattr(644,root,root,755)
/usr/local/mempooling/include/mempooling/

%changelog
* Thu May 21 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-54
- fix: For 26.0.0.1.B009_package,form sp3-br_bugfix_20260330_PR647
* Wed May 20 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-53
- fix: For 26.0.0.1.B009_package,form sp3-br_bugfix_20260330_PR631
* Mon May 18 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-52
- fix: For 26.0.0.1.B008_package,form sp3-br_bugfix_20260330_PR608
* Fri May 15 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-51
- fix: For 26.0.0.1.B008_package,form sp3-br_bugfix_20260330_PR606
* Sat May 9 2026 LI LISONG <lilisong2@huawei.com> - 1.0.0-50
- fix: For 26.0.0.1.B007_package,form PR555
* Sat May 9 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-49
- fix: For 26.0.0.1.B007_package,form PR552
* Wed May 06 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-48
- fix: For 26.0.0.1.B007_package,form PR522
* Wed April 29 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-47
- fix: For 26.0.0.1.B007_package,form PR524
* Tue April 28 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-46
- fix: For 26.1.RC1.B007_package,form PR495
* Mon Apr 27 2026 Liu Jiangqi <liuajiangqi1@huawei.com> - 1.0.0-45
- fix: dependency fix,from PR502
* Sat April 25 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-44
- fix: For JD_clos_package,form PR493
* Sat April 25 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-43
- fix: For B006_package,form PR488
* Thu April 23 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-42
- fix: For B006_package,form PR474
* Thu April 23 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-41
- fix: For B006_package,form PR470
* Wed April 22 2026 YONG WENTAO <yongwentao@huawei.com> - 1.0.0-40
- fix: For B006_package,form PR463
* Tue April 21 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-39
- fix: For B006_package,form PR450
* Tue April 21 2026 LI LISONG <lilisong2@huawei.com> - 1.0.0-38
- feat: 三方库依赖修改为依赖系统库的方式,form PR432
* Sat April 18 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-37
- fix: For JD_clos_package,form PR430
* Fri April 17 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-36
- feat: update mti interfaces to adapt cross pod
* Thu April 16 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-35
- fix: For B005_package,form PR377
* Thu April 16 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-34
- feat: support clos mesh type in container network
* Thu April 16 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-33
- fix: For B005_package,form PR406
* Mon April 13 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-32
- fix: Change bonding name from urma_x to bonding_dev_x
* Fri April 10 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-31
- fix: For B003_package,form PR365
* Thu April 09 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-30
- fix: For B003_package,form PR359
* Thu April 09 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-29
- fix: For B003_package,form PR330
* Wed April 08 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-28
- fix: For B003_package,form PR347
* Tue April 07 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-27
- fix: For B003_package,form PR333
* Thu April 02 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-26
- fix: Specify bonding name corresponding to urma info name when create bonding dev
* Wed April 01 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-25
- fix: High-safety bug
* Wed April 01 2026 YONG WENTAO <yongwentao@huawei.com> - 1.0.0-24
- fix: optimize alloc sdk invocation
* Sat Mar 28 2026 Fang JieDong <fangjiedong@h-partners.com> - 1.0.0-23
- fix: pull/289/commit
* Tue Mar 24 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-22
- fix: fixdebug
* Sun Mar 22 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-21
- fix: fix rollback 
* Thu Mar 19 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-20
- fix: fix rmrs multiNuma conf 
* Thu Mar 19 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-19
- fix: reduce threads
* Wed Mar 18 2026 Zhang Qin <zhangqin99@h-partners.com> - 1.0.0-18
- fix: reduce threads
* Tue Mar 18 2026 Li Yucheng <liyucheng22@huawei.com> - 1.0.0-17
- fix: fix rmrs bugs
* Tue Mar 17 2026 Yuan Sicheng <yuansicheng@huawei.com> - 1.0.0-16
- fix: fix ubse start
* Tue Mar 17 2026 CAO YIFAN <caoyifan9@huawei.com> - 1.0.0-15
- fix: fix ucache/rmrs spec
* Tue Mar 17 2026 LI LISONG <lilisong2@huawei.com> - 1.0.0-14
- feat: ipover URMA
* Mon Mar 16 2026 LI LISONG <lilisong2@huawei.com> - 1.0.0-13
- feat: add virt & rmrs rpm package
* Sat Mar 14 2026 LI LISONG <lilisong2@huawei.com> - 1.0.0-12
- feat: sync yellow zone code
* Wed Mar 04 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-11
- feat: update UBM listen port
* Tue March 03 2026 YONG WENTAO <yongwentao@huawei.com> - 1.0.0-10
- urma cli deleting type
* Thu Feb 26 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-9
- feat: provide hardware resource id in sdk
* Wed Feb 25 2026 Zhang Qin <zhangqin99@h-partners.com> - 1.0.0-8
- feat: update ubs-engine-1.0.0.tar.gz
* Tue Feb 24 2026 Zhu Qiucheng <zhuqiucheng@huawei.com> - 1.0.0-7
- feat(urma): support urma bounding
* Wed Feb 11 2026 Zhang Qin <zhangqin99@h-partners.com> - 1.0.0-6
- fix: update ubs-engine-1.0.0.tar.gz
* Wed Dec 10 2025 LI LISONG <lilisong2@huawei.com> - 1.0.0-5
- fix: update ubs-engine-1.0.0.tar.gz
* Tue Dec 09 2025 Wang Haoping <wanghaoping1@huawei.com> - 1.0.0-4
- fix(mem): fix bug of mti for mami
* Mon Dec 08 2025 LI LISONG <lilisong2@huawei.com> - 1.0.0-3
- fix bug of function "GetAllHandle" and Lcne
* Sat Dec 06 2025 LI LISONG <lilisong2@huawei.com> - 1.0.0-2
- lcne support updated UB protocol
* Wed Nov 26 2025 Yu Yaodong <yuyaodong2@huawei.com> - 1.0.0-1
- Package init
