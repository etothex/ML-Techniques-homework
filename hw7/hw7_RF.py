import numpy as np
import matplotlib.pyplot as plt
import sys


def read_data(file_name):
    data = []
    sign = []
    with open(file_name, 'r') as f:
        for line in f:
            items = line.strip().split()
            for i in range(len(items)):
                items[i] = float(items[i])
            data.append(items[0:-1])
            sign.append(items[-1])
    data = np.array(data)
    sign = np.array(sign)
    if data.shape[0] != sign.shape[0]:
        sys.exit(-1)
    return data, sign


def get_sign(d):                    #符号函数，大于0返回+1，否则返回-1
    sign = np.ones_like(d)
    for i, val in enumerate(d):
        if val <= 0:
            sign[i] = -1
    return sign


def get_theta(data):
    data = np.array(list(set(data)))
    theta_num = data.shape[0] - 1
    theta = np.zeros(theta_num)
    data_lh = np.sort(data)
    for i in range(theta_num):
        theta[i] = (data_lh[i] + data_lh[i+1])*0.5
    return theta


def get_err(sign_prim, sign_pred):
    if sign_prim.shape[0] != sign_pred.shape[0]:
        sys.exit(-1)
    size = sign_prim.shape[0]
    res = np.multiply(sign_pred, sign_prim)
    err_count = (size - np.sum(res))/2
    return err_count/size


def get_gini_index(s, theta, data, sign):
    sign_pred = s * get_sign(data - theta)
    c1_index = []
    c2_index = []
    for i, val in enumerate(sign_pred):
        if val == 1:
            c1_index.append(True)
            c2_index.append(False)
        elif val == -1:
            c1_index.append(False)
            c2_index.append(True)
        else:
            print('error in func gini_index:sign_pred')
            sys.exit(-1)
    c1_index = np.array(c1_index)
    c2_index = np.array(c2_index)

    sign_c1 = sign[c1_index]
    sign_c2 = sign[c2_index]
    size1 = sign_c1.shape[0]
    size2 = sign_c2.shape[0]
    sum1 = np.sum(sign_c1)
    sum2 = np.sum(sign_c2)
    impurity1 = 1 - (((size1-sum1)/(2*size1))**2 + (1-((size1-sum1)/(2*size1)))**2)
    impurity2 = 1 - (((size2-sum2)/(2*size2))**2 + (1-((size2-sum2)/(2*size2)))**2)
    gini_index = impurity1 * size1 + impurity2 * size2
    return gini_index


def dec_stump_1d(data, sign):
    theta_list = get_theta(data)
    gini_array = np.zeros((2, theta_list.shape[0]))
    for i, theta in enumerate(theta_list):
        s1 = 1
        gini_array[0][i] = get_gini_index(s1, theta, data, sign)
        s2 = -1
        gini_array[1][i] = get_gini_index(s2, theta, data, sign)

    min_0_id = np.argmin(gini_array[0])
    min_1_id = np.argmin(gini_array[1])
    min_0 = gini_array[0][min_0_id]
    min_1 = gini_array[1][min_1_id]

    if min_0 < min_1:
        gini_min = min_0
        s_best = 1
        theta_best = theta_list[min_0_id]
    else:
        gini_min = min_1
        s_best = -1
        theta_best = theta_list[min_1_id]

    return s_best, theta_best, gini_min


def branch_criterion(data_x, data_y, feature_k):
    # 随机选择feature_k个特征
    feature_ran = np.random.permutation(np.arange(0, data_x.shape[1]))
    feature_chosen = np.sort(feature_ran[0:feature_k])

    n_feature = feature_chosen.shape[0]
    s_arr = np.zeros(n_feature)
    theta_arr = np.zeros(n_feature)
    gini_arr = np.zeros(n_feature)

    for i, val in enumerate(feature_chosen):
        s_arr[i], theta_arr[i], gini_arr[i] = dec_stump_1d(data_x[:, val], data_y)

    gini_min_id = np.argmin(gini_arr)
    s_chosen = s_arr[gini_min_id]
    theta_chosen = theta_arr[gini_min_id]
    i_chosen = feature_chosen[gini_min_id]

    return s_chosen, theta_chosen, i_chosen


class Node(object):
    def __init__(self, val=(0, 0, 0)):
        # val = (s,theta,i)
        # 非叶节点，val表示decision stump的参数，用于选择分支
        # 对于叶节点，s=0,theta=optimal constant
        self.val = val
        self.Lchild = None
        self.Rchild = None


class CaRTree(object):
    def __init__(self, node=None):
        self.root = node

    def _generate_cart(self, data_x, data_y, feature_k):
        if np.abs(np.sum(data_y)) == data_y.shape[0]:
            node = Node((0, data_y[0], 0))
        else:
            s, theta, i = branch_criterion(data_x, data_y, feature_k)
            node = Node((s, theta, i))
            sign_pred = s * get_sign(data_x[:, i] - theta)  # 划分标记
            c1_index = []
            c2_index = []
            for k, val in enumerate(sign_pred):
                if val == 1:
                    c1_index.append(True)
                    c2_index.append(False)
                elif val == -1:
                    c1_index.append(False)
                    c2_index.append(True)
                else:
                    print('error in func gini_index:sign_pred')
                    sys.exit(-1)
            c1_index = np.array(c1_index)
            c2_index = np.array(c2_index)
            data_c1, sign_c1 = data_x[c1_index], data_y[c1_index]           # 数据1；划分标记为1
            data_c2, sign_c2 = data_x[c2_index], data_y[c2_index]           # 数据2：划分标记为-1
            node.Lchild = self._generate_cart(data_c1, sign_c1, feature_k)  # 左子树：划分标记为1
            node.Rchild = self._generate_cart(data_c2, sign_c2, feature_k)  # 右子树：划分标记为-1
        return node

    def build_CaRT(self, data_x, data_y, feature_k):
        self.root = self._generate_cart(data_x, data_y, feature_k)

    def get_val(self, x):
        node = self.root
        while node.val[0] != 0:     # s!=0
            s, theta, i = node.val
            res = s * get_sign(x[i:i+1] - theta)
            if res == 1:
                node = node.Lchild
            elif res == -1:
                node = node.Rchild
            else:
                print('error in CaRt.get_val:res')
                sys.exit(-1)
        else:                       # s=0(leaf node),return theta (optimal constant)
            return node.val[1]

    def predict(self, data_x):
        y_predict = np.zeros(data_x.shape[0])
        for i in range(data_x.shape[0]):
            y_predict[i] = self.get_val(data_x[i])
        return y_predict

    def draw(self):
        pass


class RandomForest(object):
    def __init__(self, sample_n, n_tree, feature_k):
        self.sample_n = sample_n
        self.n_tree = n_tree
        self.feature_k = feature_k
        self.trees = []

    def build_RF(self, data_x, data_y):
        for i in range(self.n_tree):
            index_ran = np.random.randint(0, data_x.shape[0], self.sample_n)
            sample_x, sample_y = data_x[index_ran], data_y[index_ran]
            cart = CaRTree()
            cart.build_CaRT(sample_x, sample_y, self.feature_k)
            self.trees.append(cart)

    def predict(self, data_x):
        y_predict = np.zeros((self.n_tree, data_x.shape[0]))
        for i in range(self.n_tree):
            cart = self.trees[i]
            y_predict[i] = cart.predict(data_x)
        y_rf = np.zeros(data_x.shape[0])
        for n in range(data_x.shape[0]):
            y_rf[n] = np.sum(y_predict[:, n])
        y_rf = get_sign(y_rf)
        return y_rf


if __name__ == "__main__":
    file_train = 'train.dat'
    file_test = 'test.dat'
    train_x, train_y = read_data(file_train)
    test_x, test_y = read_data(file_test)

    sample_num = train_x.shape[0]
    trees_num = 300
    feature_k = 2
    Rf = RandomForest(sample_num, trees_num, feature_k)
    Rf.build_RF(train_x, train_y)

    y_rf_train = Rf.predict(train_x)
    Ein = get_err(train_y, y_rf_train)

    y_rf_test = Rf.predict(test_x)
    Eout = get_err(test_y, y_rf_test)

    print(Ein, Eout)            # 0.0 0.072


