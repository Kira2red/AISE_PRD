$ErrorActionPreference = "Stop"

$path1 = 'f:\文档\产品文档\AISE_PRD\AISE_PRD\html\admin\渠道管理_-_AISE_后台_20251230_152723.html'
$content1 = Get-Content $path1 -Raw -Encoding UTF8

$content1 = $content1.Replace('class="hidden group-hover:inline text-[10px]"', 'class="text-[10px]"')
$content1 = $content1.Replace('平滑重置密钥', '重置密钥')

$oldBtn = '<button
                            class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-medium hover:bg-slate-200 transition flex items-center gap-1">
                            <i class="fa-solid fa-plus"></i> 新增管理员
                        </button>'
$newBtn = '<button onclick="openAddAdminModal(''add'')"
                            class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-medium hover:bg-slate-200 transition flex items-center gap-1">
                            <i class="fa-solid fa-plus"></i> 新增管理员
                        </button>'
$content1 = $content1.Replace($oldBtn, $newBtn)

$oldActions1 = '<td class="py-3 px-4 text-right">
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                    </td>'
$newActions1 = '<td class="py-3 px-4 text-right">
                                        <button onclick="resetAdminPwd()" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button onclick="openAddAdminModal(''edit'')" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                    </td>'
$content1 = $content1.Replace($oldActions1, $newActions1)

$oldActions2 = '<td class="py-3 px-4 text-right">
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                        <button class="text-slate-400 hover:text-red-500 text-xs mx-1" title="禁用"><i
                                                class="fa-solid fa-ban"></i></button>
                                    </td>'
$newActions2 = '<td class="py-3 px-4 text-right">
                                        <button onclick="resetAdminPwd()" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button onclick="openAddAdminModal(''edit'')" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                        <button onclick="toggleAdminStatus(this)" class="text-slate-400 hover:text-red-500 text-xs mx-1" title="禁用"><i
                                                class="fa-solid fa-ban"></i></button>
                                    </td>'
$content1 = $content1.Replace($oldActions2, $newActions2)

$modal = @"
    <!-- 新增/编辑管理员弹窗 -->
    <div id="modal-admin" class="fixed inset-0 z-[80] hidden flex items-center justify-center bg-slate-900/60 backdrop-blur-sm transition-opacity opacity-0">
        <div class="bg-white rounded-xl shadow-2xl w-[400px] flex flex-col transform scale-95 transition-transform" id="modal-admin-content">
            <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
                <h3 class="font-bold text-slate-800" id="admin-modal-title">新增管理员</h3>
                <button onclick="closeAddAdminModal()" class="text-slate-400 hover:text-slate-600 transition"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="p-6 space-y-4">
                <div><label class="block text-xs font-bold text-slate-600 mb-1">登录账号</label><input type="text" placeholder="输入账号名称" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm"></div>
                <div><label class="block text-xs font-bold text-slate-600 mb-1">初始密码</label><input type="password" placeholder="设置初始密码" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm"></div>
                <div><label class="block text-xs font-bold text-slate-600 mb-1">姓名 (选填)</label><input type="text" placeholder="负责人姓名" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm"></div>
                <div><label class="block text-xs font-bold text-slate-600 mb-1">手机号 (选填)</label><input type="text" placeholder="联系手机号" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm"></div>
            </div>
            <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-2 rounded-b-xl">
                <button onclick="closeAddAdminModal()" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 rounded-lg transition font-medium border border-slate-200 bg-white">取消</button>
                <button onclick="closeAddAdminModal()" class="px-4 py-2 bg-brand-600 text-white text-sm font-bold rounded-lg hover:bg-brand-700 transition">保存</button>
            </div>
        </div>
    </div>
"@

$js = @"
        // 新增/编辑管理员
        const adminModal = document.getElementById('modal-admin');
        const adminContent = document.getElementById('modal-admin-content');
        function openAddAdminModal(mode = 'add') {
            document.getElementById('admin-modal-title').innerText = mode === 'add' ? '新增管理员' : '编辑管理员';
            adminModal.classList.remove('hidden');
            setTimeout(() => { adminModal.classList.remove('opacity-0'); adminContent.classList.add('modal-enter'); }, 10);
        }
        function closeAddAdminModal() {
            adminModal.classList.add('opacity-0');
            setTimeout(() => { adminModal.classList.add('hidden'); adminContent.classList.remove('modal-enter'); }, 200);
        }
        function resetAdminPwd() {
            alert('操作演示：已为该管理员生成临时登录密码！');
        }
        function toggleAdminStatus(btn) {
            const icon = btn.querySelector('i');
            if (icon.classList.contains('fa-ban')) {
                icon.classList.replace('fa-ban', 'fa-play');
                btn.title = '启用';
                btn.classList.replace('text-red-500', 'text-green-500');
            } else {
                icon.classList.replace('fa-play', 'fa-ban');
                btn.title = '禁用';
                btn.classList.replace('text-green-500', 'text-red-500');
            }
        }
    </script>
"@

if ($content1 -notmatch 'modal-admin-content') {
    $content1 = $content1.Replace('</body>', $modal + "`n</body>")
    $content1 = $content1.Replace('</script>', $js)
}

[System.IO.File]::WriteAllText($path1, $content1, [System.Text.Encoding]::UTF8)

$path2 = 'f:\文档\产品文档\AISE_PRD\AISE_PRD\html\org_admin\05_密钥与Webhook.html'
$content2 = Get-Content $path2 -Raw -Encoding UTF8
$content2 = $content2.Replace('平滑重置密钥', '重置密钥')
[System.IO.File]::WriteAllText($path2, $content2, [System.Text.Encoding]::UTF8)

$path3 = 'f:\文档\产品文档\AISE_PRD\AISE_PRD\PRD\20260302_组织后台需求初期梳理.md'
$content3 = Get-Content $path3 -Raw -Encoding UTF8
$content3 = $content3.Replace('平滑重置', '重置')
[System.IO.File]::WriteAllText($path3, $content3, [System.Text.Encoding]::UTF8)

$path4 = 'f:\文档\产品文档\AISE_PRD\AISE_PRD\PRD\20260302_PRD_组织后台_一期.md'
$content4 = Get-Content $path4 -Raw -Encoding UTF8
$content4 = $content4.Replace('平滑重置密钥', '重置密钥')
$content4 = $content4.Replace('平滑重置', '重置')
[System.IO.File]::WriteAllText($path4, $content4, [System.Text.Encoding]::UTF8)

Write-Host "Success"
