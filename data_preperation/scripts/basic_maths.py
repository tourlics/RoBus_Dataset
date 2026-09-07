import multiprocessing

class DDA:
    def __init__(self, a, b) -> None:
        self.a = a
        self.b = b
    # DDA: pixels traversed by the line between two points
    def run(self):
        x1, y1 = (self.a[0], self.a[1])
        x2, y2 = (self.b[0], self.b[1])
        
        xDis = x2 - x1  # x increment
        yDis = y2 - y1  # y increment
        if(abs(xDis) > abs(yDis)):
            maxstep = abs(xDis)
        else:
            maxstep = abs(yDis)
        xUnitstep = xDis/maxstep  # x step increment
        yUnitstep = yDis/maxstep  # y step increment
        x = x1
        y = y1
        pointlist = []
        for k in range(maxstep):
            x = x + xUnitstep
            y = y + yUnitstep
            #print("x: %d, y:%d" % (x, y))
            pointlist.append((int(x),int(y)))
        return pointlist

def worker(pair): 
    start_point, end_point = pair   
    dda = DDA(start_point, end_point)
    dda.run()

class Point2Pix:
    def linesDDA(self,pointlist):
        allpoints = []
        pointlist = list(set(pointlist))
        if len(pointlist) == 1 : return pointlist
        for idx in range(len(pointlist)-1):
            allpoints.extend(DDA(pointlist[idx],pointlist[idx+1]).run())
        return list(set(allpoints))
        # pointlist = [(2,2),(8,8),(8,15)]
        # points = linesDDA(pointlist)
        # print(points)
    
    # def linesDDA_multiprocess(self, pointlist):  
    #     # convert pointlist to a list
    #     # create a process pool
    #     with multiprocessing.Pool(processes=4) as pool:  
    #         # rasterize all segments in parallel
    #         allpoints_lists = pool.map(worker, pointlist)  
  
    #     # merge all point lists
    #     allpoints = [point for sublist in allpoints_lists for point in sublist]  
  
    #     # drop duplicates and return
    #     return list(set(allpoints))