const defaultAccounts = [
  {
    username: 'admin',
    password: 'Admin@123',
    role: '管理员',
    displayName: '系统管理员'
  },
  {
    username: 'operator',
    password: 'Operator@123',
    role: '值班员',
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
    displayName: account.displayName,
    loginAt: new Date().toISOString()
  }
}
