const defaultAccounts = [
  {
    username: 'admin',
    password: 'Admin@123',
    role: '管理员',
    roleKey: 'admin',
    displayName: '系统管理员'
  },
  {
    username: 'operator',
    password: 'Operator@123',
    role: '员工',
    roleKey: 'employee',
    displayName: '现场值班员'
  }
]

export const loginWithDefaultAccount = (username, password) => {
  const account = defaultAccounts.find(
    (item) => item.username === username.trim() && item.password === password
  )
  if (!account) return null

  return {
    username: account.username,
    role: account.role,
    roleKey: account.roleKey,
    displayName: account.displayName,
    loginAt: new Date().toISOString()
  }
}
