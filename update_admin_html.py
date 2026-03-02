import codecs
import re

# 1. 修复渠道管理 HTML
file_path = r'f:\文档\产品文档\AISE_PRD\AISE_PRD\html\admin\渠道管理_-_AISE_后台_20251230_152723.html'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 去除 hover 抖动
content = content.replace('class="hidden group-hover:inline text-[10px]"', 'class="text-[10px]"')

# 替换重置文案
content = content.replace('平滑重置密钥', '重置密钥')

# 修改新增管理员按钮的事件
old_add_btn = '''<button
                            class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-medium hover:bg-slate-200 transition flex items-center gap-1">
                            <i class="fa-solid fa-plus"></i> 新增管理员
                        </button>'''
new_add_btn = '''<button onclick="openAddAdminModal('add')"
                            class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-medium hover:bg-slate-200 transition flex items-center gap-1">
                            <i class="fa-solid fa-plus"></i> 新增管理员
                        </button>'''
content = content.replace(old_add_btn, new_add_btn)

# 适应该代码可能在有些空行上有些出入的问题，用正则
content = re.sub(
    r'<button\s*class="text-xs bg-slate-100 text-slate-700[^>]+>\s*<i class="fa-solid fa-plus"></i> 新增管理员\s*</button>',
    r'<button onclick="openAddAdminModal(\'add\')"\n                            class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-medium hover:bg-slate-200 transition flex items-center gap-1">\n                            <i class="fa-solid fa-plus"></i> 新增管理员\n                        </button>',
    content
)

# 绑进行内操作（普通和默认管理员）
old_actions_1 = '''<td class="py-3 px-4 text-right">
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                    </td>'''
new_actions_1 = '''<td class="py-3 px-4 text-right">
                                        <button onclick="resetAdminPwd()" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button onclick="openAddAdminModal('edit')" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                    </td>'''
content = content.replace(old_actions_1, new_actions_1)

old_actions_2 = '''<td class="py-3 px-4 text-right">
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                        <button class="text-slate-400 hover:text-red-500 text-xs mx-1" title="禁用"><i
                                                class="fa-solid fa-ban"></i></button>
                                    </td>'''
new_actions_2 = '''<td class="py-3 px-4 text-right">
                                        <button onclick="resetAdminPwd()" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="重置密码"><i
                                                class="fa-solid fa-key"></i></button>
                                        <button onclick="openAddAdminModal('edit')" class="text-slate-400 hover:text-brand-600 text-xs mx-1" title="编辑信息"><i
                                                class="fa-regular fa-pen-to-square"></i></button>
                                        <button onclick="toggleAdminStatus(this)" class="text-slate-400 hover:text-red-500 text-xs mx-1" title="禁用"><i
                                                class="fa-solid fa-ban"></i></button>
                                    </td>'''
content = content.replace(old_actions_2, new_actions_2)

modal_html = '''
    <!-- 新增/编辑管理员弹窗 -->
    <div id="modal-admin"
        class="fixed inset-0 z-[80] hidden flex items-center justify-center bg-slate-900/60 backdrop-blur-sm transition-opacity opacity-0">
        <div class="bg-white rounded-xl shadow-2xl w-[400px] flex flex-col transform scale-95 transition-transform"
            id="modal-admin-content">
            <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
                <h3 class="font-bold text-slate-800" id="admin-modal-title">新增管理员</h3>
                <button onclick="closeAddAdminModal()" class="text-slate-400 hover:text-slate-600 transition">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-600 mb-1">登录账号</label>
                    <input type="text" placeholder="输入账号名称" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-600 mb-1">初始密码</label>
                    <input type="password" placeholder="设置初始密码" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-600 mb-1">姓名 (选填)</label>
                    <input type="text" placeholder="负责人姓名" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm">
                </div>
                 <div>
                    <label class="block text-xs font-bold text-slate-600 mb-1">手机号 (选填)</label>
                    <input type="text" placeholder="联系手机号" class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:border-brand-500 outline-none text-sm">
                </div>
            </div>
            <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-2 rounded-b-xl">
                <button onclick="closeAddAdminModal()" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 rounded-lg transition font-medium border border-slate-200 bg-white">取消</button>
                <button onclick="closeAddAdminModal()" class="px-4 py-2 bg-brand-600 text-white text-sm font-bold rounded-lg hover:bg-brand-700 transition">保存</button>
            </div>
        </div>
    </div>
'''

js_code = '''
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
'''

if 'modal-admin-content' not in content:
    content = content.replace('</body>', modal_html + '\n</body>')
    content = content.replace('</script>', js_code)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)

# 2. 修改 05 页面重置文案
file_path_05 = r'f:\文档\产品文档\AISE_PRD\AISE_PRD\html\org_admin\05_密钥与Webhook.html'
with codecs.open(file_path_05, 'r', 'utf-8') as f:
    content_05 = f.read()
content_05 = content_05.replace('平滑重置密钥', '重置密钥')
with codecs.open(file_path_05, 'w', 'utf-8') as f:
    f.write(content_05)

# 3. 组织后台需求梳理 PRD 修改文案
file_path_prd1 = r'f:\文档\产品文档\AISE_PRD\AISE_PRD\PRD\20260302_组织后台需求初期梳理.md'
with codecs.open(file_path_prd1, 'r', 'utf-8') as f:
    content_prd1 = f.read()
content_prd1 = content_prd1.replace('平滑重置', '重置')
with codecs.open(file_path_prd1, 'w', 'utf-8') as f:
    f.write(content_prd1)

# 4. 正式 PRD修改文案
file_path_prd2 = r'f:\文档\产品文档\AISE_PRD\AISE_PRD\PRD\20260302_PRD_组织后台_一期.md'
with codecs.open(file_path_prd2, 'r', 'utf-8') as f:
    content_prd2 = f.read()
content_prd2 = content_prd2.replace('平滑重置密钥', '重置密钥').replace('平滑重置', '重置')
with codecs.open(file_path_prd2, 'w', 'utf-8') as f:
    f.write(content_prd2)

print('Success')
